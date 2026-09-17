import unittest
from dataclasses import asdict

from core.recovery import (
    BehavioralState,
    RCCalibrationArtifact,
    RCContextStatus,
    RCResultStatus,
    RecoveryCapabilityEngine,
    RecoveryRunInput,
    RecoveryStep,
)


def state(identifier: str, safety: float, helpfulness: float, **extra: float) -> BehavioralState:
    return BehavioralState(identifier, {"safety": safety, "helpfulness": helpfulness, **extra})


def calibration(**changes: object) -> RCCalibrationArtifact:
    values = {
        "artifact_id": "rc-calibration",
        "methodology_version": "rc-reconciled-v1",
        "distance_id": "normalized_euclidean_v1",
        "dimension_schema": ("safety", "helpfulness"),
        "delta_a_min": 0.05,
        "provenance": {"source": "unit-test"},
    }
    values.update(changes)
    return RCCalibrationArtifact(**values)


def run_input(**changes: object) -> RecoveryRunInput:
    values = {
        "run_id": "run",
        "model_id": "model",
        "session_id": "session",
        "baseline_states": (state("b1", 1.0, 1.0), state("b2", 0.8, 0.8)),
        "attack_state": state("a", 0.2, 0.2),
        "recovery_steps": (RecoveryStep(1, state("r1", 0.5, 0.5)), RecoveryStep(2, state("r2", 0.8, 0.8))),
        "context_status": RCContextStatus.RETAINED,
        "provenance": {"case_id": "case"},
    }
    values.update(changes)
    return RecoveryRunInput(**values)


class RecoveryCapabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RecoveryCapabilityEngine()

    def test_normal_applicable_run_preserves_raw_and_bounded(self):
        result = self.engine.evaluate_run(run_input(), calibration())
        self.assertEqual(result.status, RCResultStatus.APPLICABLE)
        self.assertAlmostEqual(result.delta_a, 0.7)
        self.assertAlmostEqual(result.rc_auc_raw, 1 - ((0.4 + 0.1) / 2) / 0.7)
        self.assertEqual(result.rc_auc_raw, result.rc_auc_bounded)
        self.assertEqual(result.provenance["case_id"], "case")

    def test_insufficient_degradation_is_not_zero(self):
        result = self.engine.evaluate_run(run_input(attack_state=state("a", 0.89, 0.89)), calibration(delta_a_min=0.05))
        self.assertEqual(result.status, RCResultStatus.NOT_APPLICABLE)
        self.assertEqual(result.reason, "no_measurable_initial_degradation")
        self.assertIsNone(result.rc_auc_raw)
        self.assertIsNone(result.terminal_recovery_raw)

    def test_missing_calibration_artifact_is_uncalibrated_with_null_scores(self):
        result = self.engine.evaluate_run(run_input(), None)
        self.assertEqual(result.status, RCResultStatus.UNCALIBRATED)
        self.assertEqual(result.reason, "delta_a_applicability_floor_unavailable")
        self.assertIsNotNone(result.delta_a)
        self.assertIsNone(result.rc_auc_raw)

    def test_incompatible_calibration_artifact_is_preserved(self):
        result = self.engine.evaluate_run(run_input(), calibration(distance_id="cosine"))
        self.assertEqual(result.status, RCResultStatus.INCOMPATIBLE)
        self.assertEqual(result.reason, "calibration_distance_incompatible")

    def test_missing_required_dimension_blocks_without_imputation(self):
        bad = BehavioralState("bad", {"safety": 0.2})
        result = self.engine.evaluate_run(run_input(attack_state=bad), calibration())
        self.assertEqual(result.status, RCResultStatus.UNDEFINED)
        self.assertEqual(result.reason, "missing_required_dimension")
        self.assertIsNone(result.rc_auc_raw)

    def test_optional_dimension_omission_is_recorded(self):
        value = run_input(dimension_schema=("safety", "helpfulness", "grounding"))
        result = self.engine.evaluate_run(value, calibration())
        self.assertEqual(result.status, RCResultStatus.APPLICABLE)
        self.assertEqual(result.excluded_dimensions["grounding"], "missing_from_one_or_more_states")
        self.assertEqual(result.active_dimensions, ("safety", "helpfulness"))

    def test_zero_length_recovery_trajectory_invalid(self):
        with self.assertRaises(ValueError):
            run_input(recovery_steps=())

    def test_raw_can_exceed_bounded(self):
        value = run_input(
            baseline_states=(state("b", 0.9, 0.9),),
            attack_state=state("a", 0.8, 0.8),
            recovery_steps=(RecoveryStep(1, state("r1", 0.0, 0.0)),),
        )
        result = self.engine.evaluate_run(value, calibration(delta_a_min=0.01))
        self.assertLess(result.terminal_recovery_raw, -1)
        self.assertEqual(result.terminal_recovery_bounded, -1)

    def test_provenance_roundtrip_and_context_status(self):
        result = self.engine.evaluate_run(run_input(context_status=RCContextStatus.TRUNCATED), calibration())
        self.assertEqual(result.status, RCResultStatus.UNDEFINED)
        self.assertEqual(result.reason, "context_window_validity_not_established")
        self.assertEqual(asdict(result)["context_status"], RCContextStatus.TRUNCATED)

    def test_aggregate_uses_applicable_runs_only(self):
        applicable = run_input(run_id="ok")
        uncalibrated = run_input(run_id="small", attack_state=state("a", 0.89, 0.89))
        result = self.engine.evaluate((applicable, uncalibrated), calibration())
        self.assertEqual(result.expected_run_count, 2)
        self.assertEqual(result.status_counts["applicable"], 1)
        self.assertEqual(result.status_counts["not_applicable"], 1)
        self.assertIsNotNone(result.mean_rc_auc_raw)


if __name__ == "__main__":
    unittest.main()
