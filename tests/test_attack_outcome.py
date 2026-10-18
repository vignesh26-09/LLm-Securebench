import unittest

from core.evaluation import AttackOutcomeRecord, AttackOutcomeStatus, calculate_asr


class AttackOutcomeTests(unittest.TestCase):
    def test_asr_uses_only_classified_denominator(self):
        records = (
            AttackOutcomeRecord("e1", "injection", "human", "v1", True, AttackOutcomeStatus.CLASSIFIED),
            AttackOutcomeRecord("e2", "injection", "human", "v1", False, AttackOutcomeStatus.CLASSIFIED),
            AttackOutcomeRecord("e3", "injection", "human", "v1", None, AttackOutcomeStatus.AMBIGUOUS),
        )
        result = calculate_asr(records)
        self.assertEqual(result["attack_success_rate"], 0.5)
        self.assertEqual(result["denominator"], 2)
        self.assertEqual(result["excluded_counts"]["ambiguous"], 1)

    def test_nullable_outcome_contract_is_enforced(self):
        with self.assertRaises(ValueError):
            AttackOutcomeRecord("e", "injection", "human", "v1", None, AttackOutcomeStatus.CLASSIFIED)
        with self.assertRaises(ValueError):
            AttackOutcomeRecord("e", "injection", "human", "v1", True, AttackOutcomeStatus.AMBIGUOUS)


if __name__ == "__main__":
    unittest.main()
