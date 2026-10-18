"""Lossless adapters from upstream results to DRAA Mode A evidence."""

from __future__ import annotations

from dataclasses import asdict
from typing import Mapping

from core.detection.models import DetectorResult, LayerOneReport
from core.draa.models import DRAAEvidenceRecord, DRAAMode, DRAAStatus, EvidenceFeature, SeverityEvidence, Uncertainty
from core.judging.models import JudgeResult, JudgmentStatus
from core.metrics.bsda import BSDAResult, ComponentResult
from core.saea.models import ResultStatus, SAEAResult


class EvidenceExtractor:
    """Builds lossless uncalibrated evidence records; never calculates DRAA risk."""

    def build(self, *, mode: DRAAMode = DRAAMode.FEATURE_EXTRACTION, identities: Mapping[str, str | None] | None = None, layer_one: LayerOneReport | None = None, judge_results: tuple[JudgeResult, ...] = (), bsda: BSDAResult | None = None, rc: Mapping[str, object] | None = None, saea: SAEAResult | None = None, severity: SeverityEvidence | None = None, provenance: Mapping[str, object] | None = None) -> DRAAEvidenceRecord:
        identity = dict(identities or {})
        features: list[EvidenceFeature] = []
        if layer_one is not None:
            features.extend(layer_one_features(layer_one))
        features.extend(judge_features(judge_results))
        if bsda is not None:
            features.extend(bsda_features(bsda))
        if rc is not None:
            features.extend(rc_features(rc))
        if saea is not None:
            features.extend(saea_features(saea))
        return DRAAEvidenceRecord(
            evaluation_id=identity.get("evaluation_id"), case_id=identity.get("case_id"), attack_id=identity.get("attack_id"), run_id=identity.get("run_id"), sequence_id=identity.get("sequence_id"), model_id=identity.get("model_id"), dataset_id=identity.get("dataset_id"), dataset_version=identity.get("dataset_version"), threat_model=identity.get("threat_model"), mode=mode, features=tuple(features), severity=severity, provenance=dict(provenance or {}),
        )


def layer_one_features(report: LayerOneReport) -> tuple[EvidenceFeature, ...]:
    return tuple(_detector_feature(result) for result in report.detector_results) + (
        EvidenceFeature("layer1", "report_signals", {"injection": report.injection_score, "leakage": report.leakage_score, "jailbreak": report.jailbreak_score, "aggregate": report.aggregate_score, "severity": report.severity.value, "attack_success_signal": report.attack_success_signal}, "structured", "detector-native", "detector-native; not risk", DRAAStatus.APPLICABLE, provenance={"report_metadata": dict(report.metadata)}),
    )


def _detector_feature(result: DetectorResult) -> EvidenceFeature:
    return EvidenceFeature("layer1", result.detector_name, {"score": result.score, "signal_scores": dict(result.signal_scores), "matched_evidence": list(result.matched_evidence), "metadata": dict(result.metadata)}, "structured", "detector-native", "detector-native; not ground truth", DRAAStatus.APPLICABLE, confidence=result.confidence, provenance={"detector_name": result.detector_name})


def judge_features(results: tuple[JudgeResult, ...]) -> tuple[EvidenceFeature, ...]:
    output: list[EvidenceFeature] = []
    mapping = {JudgmentStatus.COMPLETED: DRAAStatus.APPLICABLE, JudgmentStatus.SKIPPED: DRAAStatus.SKIPPED, JudgmentStatus.REFUSED: DRAAStatus.REFUSED, JudgmentStatus.FAILED: DRAAStatus.FAILED}
    for result in results:
        uncertainty = Uncertainty(reason=result.uncertainty_reason) if result.uncertainty_reason else None
        output.append(EvidenceFeature("layer2", result.dimension.value, result.score, "scalar" if result.score is not None else "absent", "judge_score", "dimension/rubric-defined; not ground truth", mapping[result.status], status_reason=result.applicability_reason or result.uncertainty_reason, uncertainty=uncertainty, confidence=result.confidence, provenance={"evaluation_id": result.evaluation_id, "case_id": result.case_id, "provider": result.judge_provider, "model": result.judge_model, "model_version": result.judge_model_version, "methodology_version": result.methodology_version, "prompt_version": result.prompt_version, "rubric_version": result.rubric_version, "generation_metadata": dict(result.generation_metadata), "run_metadata": dict(result.run_metadata)}, failure=dict(result.failure) if result.failure else None))
    return tuple(output)


def bsda_features(result: BSDAResult) -> tuple[EvidenceFeature, ...]:
    components = {"semantic": result.components.semantic, "safety": result.components.safety, "instruction": result.components.instruction, "structural": result.components.structural}
    return tuple(_bsda_component(name, component, result.metadata) for name, component in components.items())


def _bsda_component(name: str, component: ComponentResult, result_metadata: Mapping[str, object]) -> EvidenceFeature:
    status = DRAAStatus.UNDEFINED if component.unmeasurable else DRAAStatus.APPLICABLE
    uncertainty = Uncertainty(confidence_interval=component.confidence_interval, reason=component.unmeasurable_reason or component.metadata.get("uncertainty_reason") if isinstance(component.metadata.get("uncertainty_reason"), str) else component.unmeasurable_reason)
    return EvidenceFeature("bsda", name, component.raw_distance, "scalar" if component.raw_distance is not None else "absent", "distance", "behavioral-change distance", status, normalized_value=component.normalized, status_reason=component.unmeasurable_reason, uncertainty=uncertainty, provenance={"calibration_status": component.calibration_status.value, "component_metadata": dict(component.metadata), "result_metadata": dict(result_metadata)})


def rc_features(rc: Mapping[str, object]) -> tuple[EvidenceFeature, ...]:
    """Preserve an RC payload supplied by an RC adapter; intentionally no inversion."""
    status = _status_from_text(rc.get("applicability") or rc.get("status"))
    reason = rc.get("reason") if isinstance(rc.get("reason"), str) else None
    provenance = {key: value for key, value in rc.items() if key not in {"rc_auc_raw", "rc_auc_bounded", "terminal_recovery_raw", "terminal_recovery_bounded", "applicability", "status", "reason", "confidence_interval"}}
    interval = _interval(rc.get("confidence_interval"))
    return tuple(EvidenceFeature("rc", name, rc.get(name), "scalar" if rc.get(name) is not None else "absent", "recovery", "higher indicates recovery; not risk", status, status_reason=reason, uncertainty=Uncertainty(confidence_interval=interval) if interval else None, provenance=provenance) for name in ("rc_auc_raw", "rc_auc_bounded", "terminal_recovery_raw", "terminal_recovery_bounded") if name in rc)


def saea_features(result: SAEAResult) -> tuple[EvidenceFeature, ...]:
    base = [
        EvidenceFeature("saea", "cv_obs", result.trajectory.cumulative_vulnerability, "scalar" if result.trajectory.cumulative_vulnerability is not None else "absent", "normalized_euclidean_distance", "sequence deviation; not risk", _saea_status(result.trajectory.status), status_reason=result.trajectory.reason, provenance={"sequence_id": result.sequence_id, "methodology_version": result.methodology_version}),
        EvidenceFeature("saea", "synergy_index", result.synergy.synergy_index, "scalar" if result.synergy.synergy_index is not None else "absent", "bliss_ratio", "candidate null-model comparison; not risk", _saea_status(result.synergy.status), status_reason=result.synergy.reason, provenance=dict(result.synergy.metadata)),
        EvidenceFeature("saea", "structured_diagnostics", {"per_step": [asdict(item) for item in result.per_step], "order_effect": asdict(result.order_effect), "shapley": asdict(result.shapley), "recovery_trend": asdict(result.recovery_trend)}, "structured", "source-native", "diagnostic", _saea_status(result.status), status_reason=result.reason),
    ]
    return tuple(base)


def _saea_status(status: ResultStatus) -> DRAAStatus:
    return _status_from_text(status.value)


def _status_from_text(value: object) -> DRAAStatus:
    text = str(value) if value is not None else "absent"
    aliases = {"applicable": DRAAStatus.APPLICABLE, "not_applicable": DRAAStatus.NOT_APPLICABLE, "uncalibrated": DRAAStatus.UNCALIBRATED, "undefined": DRAAStatus.UNDEFINED, "failed_evaluation": DRAAStatus.FAILED, "failed": DRAAStatus.FAILED, "skipped": DRAAStatus.SKIPPED, "refused": DRAAStatus.REFUSED, "insufficient_data": DRAAStatus.INSUFFICIENT_DATA, "incompatible": DRAAStatus.INCOMPATIBLE}
    return aliases.get(text, DRAAStatus.ABSENT)


def _interval(value: object) -> tuple[float, float] | None:
    if isinstance(value, (tuple, list)) and len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
        return (float(value[0]), float(value[1]))
    return None
