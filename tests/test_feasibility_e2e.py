"""P6.1 end-to-end smoke: harmless mocks, with scientific provenance blocked."""

import hashlib
import io
import json
import logging
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

from core.feasibility_pilot.allocation import Arm
from core.feasibility_pilot.restricted_store import EvidenceConflict
from scripts.feasibility_mock_smoke import FINAL_PROBE, SmokeProvider, run_mock_smoke


class FeasibilityMockE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp")
        cls.root = Path(cls.temporary.name)
        cls.recorded_commands = []
        log_stream = io.StringIO()
        log_handler = logging.StreamHandler(log_stream)
        mock_logger = logging.getLogger("core.inference.mock")
        old_level = mock_logger.level
        mock_logger.setLevel(logging.DEBUG)
        mock_logger.addHandler(log_handler)
        actual_run = subprocess.run

        def guarded_run(*args, **kwargs):
            command = args[0] if args else kwargs.get("args")
            cls.recorded_commands.append(command)
            if any("ollama" in str(part).lower() or "pip" == str(part).lower()
                   for part in (command if isinstance(command, (list, tuple)) else [command])):
                raise AssertionError("Mock integration attempted model execution or download")
            return actual_run(*args, **kwargs)

        try:
            with (patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")),
                  patch.object(urllib.request, "urlopen", side_effect=AssertionError("Network forbidden")),
                  patch.object(subprocess, "run", side_effect=guarded_run)):
                cls.artifacts = run_mock_smoke(cls.root)
            cls.captured_logs = log_stream.getvalue()
        finally:
            mock_logger.removeHandler(log_handler)
            mock_logger.setLevel(old_level)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_seven_arms_execute_and_live_assistants_are_provider_generated(self):
        artifact = self.artifacts
        self.assertIsInstance(artifact.provider, SmokeProvider)
        self.assertEqual(set(artifact.report["arms_executed"]), {item.value for item in Arm})
        self.assertEqual(artifact.report["distance_cells"], [0, 2, 5])
        self.assertEqual(artifact.report["coverage"], {
            "assigned": 12, "observed": 12, "completed": 10,
            "failed": 2, "missing": 0, "null_outcomes": 2})
        self.assertEqual({item.arm for item in artifact.assignments.assignments
                          if artifact.observations.observation(item.trial_id)["status"] == "completed"},
                         set(Arm))
        for assignment in artifact.assignments.assignments:
            row = artifact.observations.observation(assignment.trial_id)
            self.assertEqual(row["execution_provenance"], "mock_fixture")
            self.assertEqual(row["distance"], assignment.distance)
            self.assertEqual(row["matching_set_id"], assignment.matching_set_id)
            requests = [request for request in artifact.provider.conversation_requests
                        if request.conversation_id == assignment.trial_id]
            if assignment.arm == Arm.S:
                self.assertEqual(len(requests), assignment.distance + 1)
                self.assertFalse(row["live_primary_eligible_arm"])
                self.assertEqual(row["evidence_class"], "scripted_mechanism")
                continue
            for request in requests:
                prior = [message for message in request.messages if message.role == "assistant"]
                expected = []
                for step in range(sum(message.role == "user" for message in request.messages) - 1):
                    for attempt in (1, 2):
                        event = artifact.observations.read_event(
                            f"{assignment.trial_id}.turn{step}.attempt{attempt}", "response")
                        if event and event["valid_response"]:
                            expected.append(artifact.restricted.read_raw(
                                event["response_reference"]).decode())
                            break
                self.assertEqual([message.content for message in prior], expected)
        self.assertEqual(len(artifact.observations.live_primary_rows()), 6)
        self.assertTrue(all(row["arm"] != "S" for row in artifact.observations.live_primary_rows()))

    def test_filler_counts_and_final_probe_position(self):
        artifact = self.artifacts
        for item in artifact.assignments.assignments:
            row = artifact.observations.observation(item.trial_id)
            expected_distance = item.distance or 0
            self.assertEqual(row["planned_filler_exchanges"], expected_distance)
            self.assertEqual(artifact.observations.distance_schedule(item.trial_id)[
                "planned_filler_exchanges"], expected_distance)
            if row["status"] == "completed":
                self.assertEqual(row["realized_complete_filler_exchanges"], expected_distance)
                requests = [request for request in artifact.provider.conversation_requests
                            if request.conversation_id == item.trial_id]
                self.assertEqual(requests[-1].messages[-1].content, FINAL_PROBE)
            else:
                self.assertLessEqual(row["realized_complete_filler_exchanges"], expected_distance)
                self.assertIsNone(row["y_final"])
                self.assertIsNone(row["y_earlier"])
                self.assertIsNone(row["y_ever"])
        b0 = next(item for item in artifact.assignments.assignments if item.arm == Arm.B0)
        self.assertIsNone(b0.distance)
        self.assertEqual(artifact.observations.observation(b0.trial_id)["planned_filler_exchanges"], 0)

    def test_checker_retry_interruption_resume_and_immutable_records(self):
        artifact = self.artifacts
        self.assertEqual(artifact.report["outcome_fixture_checks"], {
            "both": [1, 1, 1], "earlier_only": [0, 1, 1],
            "final_only": [1, 0, 1], "interrupted": [None, None, None],
            "invalid_filler": [None, None, None]})
        retry_id = next(iter(artifact.provider.pre_submission_seen))
        first = f"{retry_id}.turn0.attempt1"
        second = f"{retry_id}.turn0.attempt2"
        self.assertIsNotNone(artifact.observations.read_event(first, "pre_submission_failure"))
        self.assertIsNotNone(artifact.observations.read_event(second, "response"))
        self.assertEqual(artifact.restricted.read_raw(first + ".request"),
                         artifact.restricted.read_raw(second + ".request"))
        interrupted_id = next(iter(artifact.provider.interrupted_seen))
        interrupted = artifact.observations.observation(interrupted_id)
        self.assertEqual(interrupted["reason"], "delivery_uncertain_no_retry")
        self.assertEqual(sum(tid == interrupted_id for tid, _ in artifact.provider.generated), 0)
        invalid_id = next(tid for tid, mode in artifact.provider.modes.items()
                          if mode == "invalid_filler")
        invalid = artifact.observations.observation(invalid_id)
        self.assertEqual(invalid["reason"], "invalid_or_incomplete_response")
        self.assertEqual(invalid["realized_complete_filler_exchanges"], 0)
        pair = next(item for item in artifact.assignments.assignments if item.trial_id == invalid_id)
        counterpart = next(item for item in artifact.assignments.assignments
                           if item.matching_set_id == pair.matching_set_id and item.arm == Arm.T)
        self.assertEqual(pair.matching_set_id, counterpart.matching_set_id)
        self.assertEqual(artifact.observations.observation(counterpart.trial_id)["status"], "completed")
        with self.assertRaises(EvidenceConflict) as caught:
            artifact.observations.complete(counterpart.trial_id, {
                **artifact.observations.observation(counterpart.trial_id), "y_final": 1})
        artifact.restricted.assert_public_safe(str(caught.exception))

    def test_context_gate_pair_asymmetry_and_mock_provenance(self):
        artifact = self.artifacts
        report = artifact.report
        self.assertEqual(report["context_status_counts"], {
            "retained_verified": 0, "truncated_known": 1,
            "retention_unverifiable": 11})
        self.assertEqual(report["at_context_pairs"]["assigned_pairs"], 3)
        self.assertEqual(report["at_context_pairs"]["asymmetric_pairs"], 2)
        self.assertTrue(report["at_context_pairs"]["differential_validity_warning"])
        self.assertEqual(len(report["at_context_pair_rows"]), 3)
        self.assertTrue(any(row["a_status"] == "truncated_known" and
                            row["t_status"] == "retention_unverifiable"
                            for row in report["at_context_pair_rows"]))
        self.assertEqual(report["verified_context_primary_rows"], 0)
        self.assertEqual(artifact.observations.verified_context_primary_rows(), ())
        self.assertFalse(report["scientific_pilot_evidence"])
        self.assertEqual(report["evidence_class"], "mock_fixture")
        self.assertEqual(report["originality_gate"], "G1_STOP")
        self.assertEqual(report["real_model_generation_calls"], 0)
        self.assertEqual(report["model_downloads"], 0)
        self.assertFalse(any("ollama" in str(cmd).lower() for cmd in self.recorded_commands))

    def test_restricted_secret_and_source_hashes_never_enter_public_outputs(self):
        artifact = self.artifacts
        public = "\n".join(path.read_text(encoding="utf-8")
                           for path in (self.root / "public").rglob("*.json"))
        report_text = json.dumps(artifact.report, sort_keys=True)
        artifact.restricted.assert_public_safe(public + report_text + self.captured_logs)
        public_projection = json.dumps(artifact.restricted.export_public(), sort_keys=True)
        artifact.restricted.assert_public_safe(public_projection)
        for item in artifact.assignments.assignments:
            secret = artifact.restricted.read_raw(item.secret_reference).decode()
            self.assertNotIn(secret, public)
            self.assertNotIn(secret, report_text)
            self.assertNotIn(secret, self.captured_logs)
            self.assertNotIn(secret, public_projection)
            for path in (self.root / "restricted" / "raw").glob("*.json"):
                self.assertNotIn(secret, path.read_text(encoding="utf-8"))
        for relative, expected in artifact.report["source_sha256"].items():
            source = Path(__file__).resolve().parents[1] / relative
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), expected)
        self.assertGreater(artifact.report["restricted_record_count"], 12)


if __name__ == "__main__":
    unittest.main()
