import unittest
from pathlib import Path

from scripts.production_preflight import assess


class ProductionPreflightTests(unittest.TestCase):
    def test_reports_missing_research_inputs_without_fabricating_eligibility(self):
        path = Path(__file__)
        result = assess(
            {"metadata": {"version": "0.1"}, "records": [{"id": "a", "prompt": "test", "category": "benign"}]},
            path=path,
            inventory=[{"name": "qwen3.5:2b"}],
            requested_models=["qwen3.5:2b", "mistral:7b"],
            minimum_cases=100,
        )
        self.assertFalse(result["eligible_for_production_execution"])
        self.assertIn("dataset_requires_at_least_100_cases", result["blockers"])
        self.assertIn("independent_label_schema_id_missing", result["blockers"])
        self.assertIn("requested_models_not_installed:mistral:7b", result["blockers"])

    def test_accepts_complete_operational_inputs_but_does_not_validate_science(self):
        path = Path(__file__)
        result = assess(
            {"metadata": {"version": "1", "source": "approved-source", "provenance": {"approval_id": "a", "outcome_protocol_id": "o", "label_schema_id": "l", "rater_protocol_id": "r"}},
             "records": [{"id": str(i), "prompt": "test", "category": "benign"} for i in range(3)]},
            path=path, inventory=[{"name": "qwen"}, {"name": "gemma"}], requested_models=["qwen", "gemma"], minimum_cases=3,
        )
        self.assertTrue(result["eligible_for_production_execution"])
        self.assertFalse(result["scientifically_validated"])
