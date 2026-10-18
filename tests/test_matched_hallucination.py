"""Fixture-only verification of the proposed paired factual-error metric."""

import unittest

from pydantic import ValidationError

from core.metrics.matched_hallucination import (
    FactualObservation, MatchedFactualPair, compute_matched_hallucination_lift,
)


HASH = "a" * 64


def observation(pair_id, arm, outcome, *, context="retained_verified", model="model-a"):
    return FactualObservation(
        observation_id=f"{pair_id}:{arm}", arm=arm, model_id=model,
        question_id=pair_id, reference_sha256=HASH, configuration_id="config-v1",
        context_status=context, outcome=outcome,
        label_id=f"review:{pair_id}:{arm}" if outcome in {"hallucinated", "verified_no_hallucination"} else None,
        label_source="human_adjudicated" if outcome in {"hallucinated", "verified_no_hallucination"} else None,
    )


def pair(pair_id, a="hallucinated", b="verified_no_hallucination", *, a_context="retained_verified"):
    return MatchedFactualPair(
        pair_id=pair_id, model_id="model-a", question_id=pair_id,
        reference_sha256=HASH, configuration_id="config-v1",
        adversarial=observation(pair_id, "adversarial", a, context=a_context) if a else None,
        topic_matched_benign=observation(pair_id, "topic_matched_benign", b) if b else None,
    )


class MatchedHallucinationTests(unittest.TestCase):
    def test_complete_pair_lift_and_all_assigned_bounds(self):
        result = compute_matched_hallucination_lift((
            pair("p1"), pair("p2", "verified_no_hallucination", "verified_no_hallucination"),
            pair("p3", "hallucinated", None), pair("p4", None, None),
        ))
        self.assertEqual(result.assigned_pairs, 4)
        self.assertEqual(result.complete_context_valid_pairs, 2)
        self.assertEqual(result.complete_pair_lift, 0.5)
        self.assertEqual(result.adversarial_rate_complete, 0.5)
        self.assertEqual(result.benign_rate_complete, 0.0)
        self.assertEqual(result.assigned_population_lower_bound, 0.0)
        self.assertEqual(result.assigned_population_upper_bound, 0.75)
        self.assertEqual(result.incomplete_pairs, 2)

    def test_no_complete_pairs_remains_insufficient_and_unknown_is_not_zero(self):
        result = compute_matched_hallucination_lift((pair("p1", "ambiguous", None),))
        self.assertEqual(result.status, "insufficient_data")
        self.assertIsNone(result.complete_pair_lift)
        self.assertEqual((result.assigned_population_lower_bound,
                          result.assigned_population_upper_bound), (-1.0, 1.0))
        self.assertEqual(result.ambiguous_or_unavailable_observations, 1)
        empty = compute_matched_hallucination_lift(())
        self.assertIsNone(empty.assigned_population_lower_bound)

    def test_truncated_context_is_not_eligible_even_with_a_human_label(self):
        result = compute_matched_hallucination_lift((pair("p1", a_context="truncated_known"),))
        self.assertEqual(result.context_invalid_observations, 1)
        self.assertIsNone(result.complete_pair_lift)
        self.assertEqual((result.assigned_population_lower_bound,
                          result.assigned_population_upper_bound), (0.0, 1.0))

    def test_rejects_unlabeled_binary_result_and_mismatched_or_duplicate_pairs(self):
        with self.assertRaises(ValidationError):
            FactualObservation(observation_id="x", arm="adversarial", model_id="model-a",
                               question_id="q", reference_sha256=HASH, configuration_id="config-v1",
                               context_status="retained_verified", outcome="hallucinated")
        with self.assertRaises(ValidationError):
            MatchedFactualPair(pair_id="p1", model_id="model-a", question_id="p1",
                               reference_sha256=HASH, configuration_id="config-v1",
                               adversarial=observation("p1", "adversarial", "hallucinated", model="other"))
        with self.assertRaises(ValueError):
            compute_matched_hallucination_lift((pair("p1"), pair("p1")))


if __name__ == "__main__":
    unittest.main()
