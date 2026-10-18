import unittest

from core.detection.models import LayerOneReport, Severity
from core.metrics.model_scoring import ml_readiness_payload, score_evaluation, score_model_run


class ModelScoringTests(unittest.TestCase):
    def test_model_score_uses_declared_detector_formula(self):
        first = score_evaluation(
            evaluation_id="e1",
            case_id="c1",
            report=LayerOneReport((), 0.3, 0.0, 0.0, 0.1, Severity.NONE, None),
        )
        second = score_evaluation(
            evaluation_id="e2",
            case_id="c2",
            report=LayerOneReport((), 0.0, 0.6, 0.0, 0.2, Severity.LOW, None),
        )
        result = score_model_run(run_id="run", model_name="model", total_evaluations=2, evaluation_scores=(first, second))
        self.assertAlmostEqual(first.threat_score, 0.1)
        self.assertAlmostEqual(second.threat_score, 0.2)
        self.assertAlmostEqual(result.mean_threat_score, 0.15)
        self.assertAlmostEqual(result.model_score, 0.85)
        self.assertEqual(result.coverage, 1.0)
        self.assertIn("model_score", result.formula)
        self.assertEqual(result.status, "engineering_only")
        self.assertIn("not_a_calibrated_safety_metric", result.warnings)

    def test_ml_readiness_blocks_without_independent_labels(self):
        payload = ml_readiness_payload(run_id="run", target_labels_available=False)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "no_independent_outcome_labels")
        self.assertIn("l2_logistic_regression", payload["allowed_estimators"])


if __name__ == "__main__":
    unittest.main()
