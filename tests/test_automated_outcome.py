import json
import unittest

from core.evaluation.automated_outcome import (AutomatedOutcomeEvaluator,
    OutcomeEvaluationCase, parse_outcome_output)
from core.judging.mock import MockJudgeProvider
from core.judging.models import JudgeConfig


class AutomatedOutcomeTests(unittest.TestCase):
    def test_structured_measurement_preserves_evidence_and_unvalidated_status(self):
        raw = json.dumps({"outcome": "partial", "confidence": 0.6,
                          "reason": "Synthetic objective partly met", "evidence": ["synthetic excerpt"]})
        provider = MockJudgeProvider([raw])
        config = JudgeConfig("mock-judge", "mock-model", "test", "outcome-v1", "prompt-v1", "rubric-v1")
        case = OutcomeEvaluationCase("synthetic-e1", "Safe task", "Synthetic objective", "Sample response",
                                     ({"role": "user", "content": "Synthetic prompt"},), "synthetic", "test")
        result = AutomatedOutcomeEvaluator(provider, config, rubric="Synthetic test rubric").evaluate(case)
        self.assertEqual(result.outcome, "partial")
        self.assertEqual(result.status, "measured")
        self.assertEqual(result.evidence, ("synthetic excerpt",))
        self.assertEqual(result.label_source, "automated_evaluator_unvalidated")
        self.assertIn("adversarial_objective", provider.requests[0].prompt)

    def test_invalid_or_dimension_only_output_is_unavailable_not_success(self):
        provider = MockJudgeProvider([json.dumps({"dimension": "safety", "score": 0.9})])
        config = JudgeConfig("mock-judge", "mock-model", "test", "outcome-v1", "prompt-v1", "rubric-v1")
        case = OutcomeEvaluationCase("synthetic-e2", "Safe task", "Synthetic objective", "Sample response", (), "synthetic", "test")
        result = AutomatedOutcomeEvaluator(provider, config, rubric="Synthetic rubric").evaluate(case)
        self.assertEqual(result.outcome, "unavailable")
        self.assertEqual(result.status, "failed")
        self.assertIsNone(result.confidence)
        with self.assertRaisesRegex(ValueError, "confidence"):
            parse_outcome_output(json.dumps({"outcome": "success", "confidence": True,
                                             "reason": "Synthetic", "evidence": []}))


if __name__ == "__main__":
    unittest.main()
