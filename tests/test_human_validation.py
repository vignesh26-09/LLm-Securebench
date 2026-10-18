import unittest

from core.evaluation import RaterLabel, agreement_rate, cohens_kappa, confusion_matrix, export_blinded_samples, fleiss_kappa


class HumanValidationTests(unittest.TestCase):
    def test_blinded_export_is_deterministic_and_retains_join_key(self):
        rows = [{"evaluation_id": "e1", "prompt": "p", "response": "r"}]
        first = export_blinded_samples(rows, salt="s", dimension="safety")
        second = export_blinded_samples(rows, salt="s", dimension="safety")
        self.assertEqual(first, second)
        self.assertEqual(first[0].evaluation_id, "e1")
        self.assertNotEqual(first[0].blinded_id, "e1")

    def test_agreement_and_cohens_kappa(self):
        labels = (
            RaterLabel("a", "r1", "safety", "pass"),
            RaterLabel("a", "r2", "safety", "pass"),
            RaterLabel("b", "r1", "safety", "fail"),
            RaterLabel("b", "r2", "safety", "pass"),
        )
        self.assertEqual(agreement_rate(labels)["agreement_rate"], 0.5)
        result = cohens_kappa(labels)
        self.assertEqual(result["status"], "computed")
        self.assertIn("kappa", result)

    def test_fleiss_requires_three_raters_and_confusion_matrix(self):
        few = (RaterLabel("a", "r1", "safety", "pass"), RaterLabel("a", "r2", "safety", "pass"))
        self.assertEqual(fleiss_kappa(few)["status"], "not_applicable")
        labels = few + (RaterLabel("a", "r3", "safety", "fail"),)
        self.assertEqual(fleiss_kappa(labels)["status"], "computed")
        matrix = confusion_matrix((RaterLabel("a", "human", "safety", "pass"),), (RaterLabel("a", "judge", "safety", "fail"),))
        self.assertEqual(matrix["matrix"]["pass"]["fail"], 1)


if __name__ == "__main__":
    unittest.main()
