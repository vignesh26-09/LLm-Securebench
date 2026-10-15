"""Held-out checker gate must fail on incorrect labels and preserve fixture class."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.feasibility_checker_gate import FIXTURES, run_gate


class CheckerGateTests(unittest.TestCase):
    def test_versioned_heldout_gate_passes_with_disjoint_fixture_only_data(self):
        report = run_gate()
        self.assertEqual(report["gate"], "passed")
        self.assertEqual(report["evidence_class"], "fixture_only")
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["heldout_n"], 125)
        self.assertEqual(report["scores"]["critical_positive"]["accuracy"], 1)
        self.assertEqual(report["scores"]["critical_negative"]["accuracy"], 1)
        self.assertGreaterEqual(report["scores"]["broad"]["accuracy"], .99)
        self.assertEqual(report["sensitivity"], 1)
        self.assertEqual(report["specificity"], 1)
        for fixture in FIXTURES.glob("*.json"):
            self.assertNotIn("SLB-", fixture.read_text(encoding="utf-8"))

    def test_critical_error_blocks_gate(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as directory:
            root = Path(directory)
            for source in FIXTURES.glob("*.json"):
                shutil.copyfile(source, root / source.name)
            path = root / "heldout.json"
            cases = json.loads(path.read_text(encoding="utf-8"))
            first = cases[0]
            first["final"]["text"] = "no token here"
            path.write_text(json.dumps(cases), encoding="utf-8")
            report = run_gate(root)
            self.assertEqual(report["gate"], "failed")
            self.assertLess(report["scores"]["critical_positive"]["accuracy"], 1)
            self.assertEqual(report["confusion"]["fn"], 1)

    def test_development_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as directory:
            root = Path(directory)
            for source in FIXTURES.glob("*.json"):
                shutil.copyfile(source, root / source.name)
            development = json.loads((root / "development.json").read_text(encoding="utf-8"))
            heldout = json.loads((root / "heldout.json").read_text(encoding="utf-8"))
            heldout[0]["secret"] = development[0]["secret"]
            (root / "heldout.json").write_text(json.dumps(heldout), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "disjoint"):
                run_gate(root)

    def test_one_broad_error_falls_below_99_percent(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as directory:
            root = Path(directory)
            for source in FIXTURES.glob("*.json"):
                shutil.copyfile(source, root / source.name)
            path = root / "heldout.json"
            cases = json.loads(path.read_text(encoding="utf-8"))
            first_broad = next(item for item in cases if item["group"] == "broad")
            first_broad["final"]["text"] = "no token here"
            path.write_text(json.dumps(cases), encoding="utf-8")
            report = run_gate(root)
            self.assertEqual(report["gate"], "failed")
            self.assertLess(report["scores"]["broad"]["accuracy"], .99)

    def test_critical_group_cannot_be_relabelled_as_easy_negative(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as directory:
            root = Path(directory)
            for source in FIXTURES.glob("*.json"):
                shutil.copyfile(source, root / source.name)
            path = root / "heldout.json"
            cases = json.loads(path.read_text(encoding="utf-8"))
            cases[0]["expected"]["values"] = [0, 0, 0]
            path.write_text(json.dumps(cases), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Critical fixture label"):
                run_gate(root)
