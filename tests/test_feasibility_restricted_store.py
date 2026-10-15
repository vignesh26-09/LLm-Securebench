"""Real Windows ACL/DPAPI tests use disposable harmless evidence only."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.feasibility_pilot.restricted_store import (
    EvidenceConflict, EvidenceSecurityError, RestrictedEvidenceStore,
    _acl_details, _current_user_sid)


TEMP_ROOT = Path(r"F:\SecureLLM.tmp")


class RestrictedStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.store = RestrictedEvidenceStore(Path(self.temporary.name) / "restricted")

    def test_acl_key_separation_encryption_and_public_projection(self):
        for directory in (self.store.root, self.store.root / "keys", self.store.root / "raw"):
            acl = _acl_details(directory)
            self.assertTrue(acl["Protected"])
            self.assertEqual({rule["Sid"] for rule in acl["Rules"]},
                             {_current_user_sid(), "SY", "BA"})
            self.assertFalse(any(rule["Inherited"] for rule in acl["Rules"]))
        secret = b"FIXTURE-ALPHA-KEY"
        projection = self.store.append_raw("secret.trial_1", "trial_1", "secret", secret)
        raw_file = self.store.root / "raw" / "secret.trial_1.json"
        self.assertNotIn(secret, raw_file.read_bytes())
        self.assertNotIn(secret, json.dumps(self.store.export_public()).encode())
        self.assertEqual(self.store.read_raw("secret.trial_1"), secret)
        self.assertEqual(projection["trial_id"], "trial_1")
        self.assertTrue((self.store.root / "keys" / "master.v1.dpapi").exists())
        self.assertFalse((self.store.root / "raw" / "master.v1.dpapi").exists())
        with self.assertRaises(EvidenceSecurityError):
            self.store.assert_public_safe("response " + secret.decode())

    def test_duplicate_is_idempotent_only_for_same_verified_content(self):
        first = self.store.append_raw("response_1", "trial_1", "response", b"harmless answer")
        self.assertEqual(first, self.store.append_raw(
            "response_1", "trial_1", "response", b"harmless answer"))
        with self.assertRaises(EvidenceConflict):
            self.store.append_raw("response_1", "trial_1", "response", b"different")
        amended = self.store.append_raw("response_2", "trial_1", "response", b"amendment",
                                         version=2, previous_id="response_1")
        self.assertEqual(amended["previous_id"], "response_1")
        self.assertEqual(self.store.read_raw("response_1"), b"harmless answer")

    def test_ciphertext_and_key_tamper_fail_without_echoing_payload(self):
        self.store.append_raw("response_1", "trial_1", "response", b"harmless answer")
        path = self.store.root / "raw" / "response_1.json"
        envelope = json.loads(path.read_text())
        envelope["ciphertext"] = "AAAA"
        path.write_text(json.dumps(envelope))
        with self.assertRaises(EvidenceSecurityError) as raised:
            self.store.read_raw("response_1")
        self.assertNotIn("harmless answer", str(raised.exception))
        key = self.store.root / "keys" / "master.v1.dpapi"
        key.write_bytes(b"tampered")
        with self.assertRaises(EvidenceSecurityError):
            RestrictedEvidenceStore(self.store.root)

    def test_public_scan_rejects_secret_even_in_model_output(self):
        secret = "FIXTURE-ALPHA-KEY"
        self.store.append_raw("secret.trial_1", "trial_1", "secret", secret.encode())
        self.store.append_raw("response_1", "trial_1", "response", secret.encode())
        self.assertNotIn(secret, json.dumps(self.store.export_public()))
        with self.assertRaises(EvidenceSecurityError):
            self.store.assert_public_safe(json.dumps({"model_output": secret}))

    def test_reopened_raw_file_with_broadened_acl_is_rejected(self):
        self.store.append_raw("response_1", "trial_1", "response", b"fixture only")
        path = self.store.root / "raw" / "response_1.json"
        subprocess.run(["icacls", str(path), "/grant", "*S-1-1-0:R"],
                       check=True, capture_output=True)
        with self.assertRaises(EvidenceSecurityError):
            self.store.read_raw("response_1")

    def test_restricted_path_is_git_ignored(self):
        result = subprocess.run(["git", "check-ignore", "-q",
                                 "experiments/feasibility_pilot/restricted/sample.json"],
                                cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(result.returncode, 0)
