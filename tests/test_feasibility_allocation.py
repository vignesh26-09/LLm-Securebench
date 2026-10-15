"""Frozen allocation and development-derived matching fixture checks."""

from dataclasses import replace
import unittest

from core.feasibility_pilot.allocation import (AllocationLedger, Arm, DISTANCES,
    allocate_trial, counterbalanced_variant, validate_at_pairs)
from core.feasibility_pilot.matching import (NumericTolerance, PlannedHistory,
                                              compare_planned)
from core.feasibility_pilot.restricted_store import EvidenceConflict


def trial(arm=Arm.A, distance=2, variant="p1"):
    return allocate_trial(protocol_sha256="f" * 64, model_id="mock-model", goal_id="g1",
                          repetition=1, arm=arm, distance=distance,
                          probe_variant_id=variant, probe_version=1,
                          seed=7, script_version="fixture-v1")


class AllocationTests(unittest.TestCase):
    def test_all_seven_arms_and_pair_stability(self):
        self.assertEqual(set(DISTANCES), set(Arm))
        self.assertEqual(DISTANCES[Arm.B0], {None})
        with self.assertRaises(ValueError):
            trial(Arm.B0, 0)
        all_trials = tuple(trial(arm, None if arm == Arm.B0 else 2) for arm in Arm)
        self.assertEqual(len({item.trial_id for item in all_trials}), 7)
        self.assertEqual(len({item.secret_reference for item in all_trials}), 7)
        self.assertEqual(trial().matching_set_id, trial(Arm.T, variant="p2").matching_set_id)
        validate_at_pairs((trial(), trial(Arm.T, variant="p2")))
        with self.assertRaises(ValueError):
            validate_at_pairs((trial(),))
        with self.assertRaises(ValueError):
            validate_at_pairs((trial(), trial(Arm.T)))
        self.assertFalse(trial(Arm.S).live_primary_eligible_arm)

    def test_freeze_and_counterbalance_without_outcomes(self):
        ledger = AllocationLedger()
        ledger.add(trial())
        ledger.add(trial(Arm.T, variant="p2"))
        old_hash = ledger.freeze()
        self.assertEqual(old_hash, ledger.sha256)
        with self.assertRaises(EvidenceConflict):
            ledger.add(trial(Arm.R))
        self.assertNotEqual(counterbalanced_variant(("p1", "p2"), 1, Arm.A, seed=7),
                            counterbalanced_variant(("p1", "p2"), 1, Arm.T, seed=7))

    def test_exact_planned_and_numeric_matching_with_preapproval_gate(self):
        tolerance = NumericTolerance("mock-model", 5, .1, .02, "d" * 64)
        with self.assertRaises(ValueError):
            tolerance.require_real_execution_approval()
        base = PlannedHistory("mock-model", "g1", "task", "family", "topic-reviewed",
                              3, ("user", "assistant") * 3, 1, 5, "c" * 64,
                              "script-a", 100, .4)
        self.assertTrue(compare_planned(base, replace(base, planned_tokens=104), tolerance).matched)
        mismatch = compare_planned(base, replace(base, goal_id="g2", planned_tokens=120),
                                   tolerance)
        self.assertIn("goal_id_mismatch", mismatch.reasons)
        self.assertIn("token_absolute_mismatch", mismatch.reasons)

