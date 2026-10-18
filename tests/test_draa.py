"""CPU-only deterministic tests for uncalibrated DRAA evidence preservation."""

import unittest

from core.detection.models import DetectorResult, LayerOneReport, Severity
from core.draa import EvidenceExtractor
from core.draa.diagnostics import correlation_ready_series, summarize
from core.draa.models import (
    DRAACalibrationArtifact, DRAAMode, DRAAStatus, SeverityEvidence,
)
from core.draa.serialization import dumps, loads
from core.judging.models import JudgeDimension, JudgeLabel, JudgeResult, JudgmentStatus
from core.metrics.bsda import BSDAComponents, BSDAResult, CalibrationStatus, ComponentResult, ThreatModel
from core.saea.models import (
    AttackInstance, BehavioralState, ContextStatus, ResultStatus, SAEAInput,
    SpacingCondition,
)
from core.saea.engine import SAEAEngine


def component(value: float | None, *, unavailable: bool = False) -> ComponentResult:
    return ComponentResult(value, None, CalibrationStatus.UNCALIBRATED, None, None, unavailable, "missing" if unavailable else None, {})


def bsda() -> BSDAResult:
    return BSDAResult(ThreatModel.JAILBREAK, 1, BSDAComponents(component(0.1), component(0.2), component(0.3), component(None, unavailable=True)))


def judge(status: JudgmentStatus = JudgmentStatus.COMPLETED) -> JudgeResult:
    completed = status is JudgmentStatus.COMPLETED
    return JudgeResult("eval", "case", JudgeDimension.SAFETY_STANCE, status, completed, None if completed else "not_applicable", "mock", "mock-model", "v1", "method", "prompt", "rubric", 0.7 if completed else None, JudgeLabel.PASS if completed else None, 0.8 if completed else None, None, "brief" if completed else None, (), {}, {}, "now", 1, {"type": "timeout"} if status is JudgmentStatus.FAILED else None)


def saea() -> object:
    baseline = BehavioralState("b", {"safety": 0.0, "helpfulness": 0.0})
    attack_state = BehavioralState("a", {"safety": 0.4, "helpfulness": 0.4})
    isolated = BehavioralState("i", {"safety": 0.0, "helpfulness": 0.0})
    attack = AttackInstance("a1", "a", "safe", "test", 1, "case", attack_state, isolated, (baseline,))
    return SAEAEngine().evaluate(SAEAInput("run", "seq", "mock", "data", "v1", (baseline,), (attack,), SpacingCondition.STACKED, ContextStatus.RETAINED))


class DRAATest(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = EvidenceExtractor()

    def test_layer_one_and_layer_two_statuses_preserved(self) -> None:
        report = LayerOneReport((DetectorResult("keyword", 0.5, ("synthetic",), 0.6, {"jailbreak": 0.5}),), 0.0, 0.0, 0.5, 0.2, Severity.LOW, None)
        record = self.extractor.build(layer_one=report, judge_results=(judge(), judge(JudgmentStatus.FAILED), judge(JudgmentStatus.SKIPPED), judge(JudgmentStatus.REFUSED)))
        self.assertEqual(record.status, DRAAStatus.UNCALIBRATED)
        self.assertIsNone(record.risk_score)
        self.assertEqual([f.status for f in record.features if f.namespace == "layer2"], [DRAAStatus.APPLICABLE, DRAAStatus.FAILED, DRAAStatus.SKIPPED, DRAAStatus.REFUSED])
        self.assertEqual(next(f for f in record.features if f.name == "keyword").raw_value["score"], 0.5)

    def test_bsda_rc_and_severity_are_not_aggregated(self) -> None:
        record = self.extractor.build(bsda=bsda(), rc={"rc_auc_raw": 0.8, "rc_auc_bounded": 0.8, "applicability": "applicable", "context_truncation_status": "retained"}, severity=SeverityEvidence("severe", "taxonomy-v1", "expert"))
        components = [f for f in record.features if f.namespace == "bsda"]
        self.assertEqual(len(components), 4)
        self.assertEqual(components[-1].status, DRAAStatus.UNDEFINED)
        rc_raw = next(f for f in record.features if f.name == "rc_auc_raw")
        self.assertEqual(rc_raw.raw_value, 0.8)
        self.assertIn("higher indicates recovery", rc_raw.orientation)
        self.assertEqual(record.severity.raw_value, "severe")

    def test_rc_not_applicable_and_context_are_preserved_without_imputation(self) -> None:
        record = self.extractor.build(rc={"rc_auc_raw": None, "terminal_recovery_raw": None, "applicability": "not_applicable", "reason": "no_measurable_initial_degradation", "context_truncation_status": "truncated"})
        feature = next(f for f in record.features if f.name == "rc_auc_raw")
        self.assertIsNone(feature.raw_value)
        self.assertEqual(feature.status, DRAAStatus.NOT_APPLICABLE)
        self.assertEqual(feature.provenance["context_truncation_status"], "truncated")

    def test_saea_undefined_si_and_diagnostics_are_preserved(self) -> None:
        record = self.extractor.build(saea=saea())
        si = next(f for f in record.features if f.name == "synergy_index")
        self.assertIsNone(si.raw_value)
        self.assertEqual(si.status, DRAAStatus.NOT_APPLICABLE)
        diagnostics = next(f for f in record.features if f.name == "structured_diagnostics")
        self.assertIn("per_step", diagnostics.raw_value)

    def test_mode_b_diagnostics_and_serialization_are_deterministic(self) -> None:
        first = self.extractor.build(mode=DRAAMode.UNCALIBRATED_DIAGNOSTICS, identities={"evaluation_id": "e", "run_id": "r"}, bsda=bsda(), provenance={"source": "fixture"})
        second = self.extractor.build(mode=DRAAMode.UNCALIBRATED_DIAGNOSTICS, identities={"evaluation_id": "e", "run_id": "r"}, bsda=bsda(), provenance={"source": "fixture"})
        self.assertEqual(first, second)
        self.assertEqual(loads(dumps(first)), first)
        self.assertEqual(summarize((first,)).status_counts["applicable"], 3)
        self.assertEqual(correlation_ready_series((first,))["bsda.semantic"], (0.1,))

    def test_calibration_artifact_is_schema_only(self) -> None:
        artifact = DRAACalibrationArtifact("a", "method", "model", "labels", {"bsda": "v1"}, ("bsda.semantic",), {}, {}, {}, None, None, None, None, {}, {}, "unvalidated")
        self.assertEqual(artifact.validation_status, "unvalidated")


if __name__ == "__main__":
    unittest.main()
