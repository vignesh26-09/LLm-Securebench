"""Deterministic contract-level feature admissibility checks."""

from __future__ import annotations

from dataclasses import dataclass

from core.prediction.models import FeatureDefinition, FeatureRecord, FeatureSchema, PredictionStage, PredictionTask


_STAGE_ORDER = {
    PredictionStage.PRE_PROMPT_STATIC: 0,
    PredictionStage.PRE_GENERATION: 1,
    PredictionStage.POST_RESPONSE: 2,
    PredictionStage.HISTORICAL_SESSION: 3,
    PredictionStage.POST_SESSION: 4,
    PredictionStage.MODEL_LEVEL_HISTORICAL: 5,
}


@dataclass(frozen=True, slots=True)
class AdmissibilityResult:
    accepted: bool
    reason: str | None = None
    warning: str | None = None


def check_feature(task: PredictionTask, schema: FeatureSchema, record: FeatureRecord) -> AdmissibilityResult:
    """Check declared provenance and timing; this is not statistical leakage discovery."""
    if schema.prediction_task_id != task.task_id:
        return AdmissibilityResult(False, "feature_schema_task_mismatch")
    definition = _definition(schema, record.feature_name)
    if definition is None:
        return AdmissibilityResult(False, "feature_not_in_schema")
    if record.source_namespace != definition.source_namespace or record.value_type != definition.expected_type:
        return AdmissibilityResult(False, "feature_contract_mismatch")
    if not definition.admissible:
        return AdmissibilityResult(False, definition.admissibility_reason or "feature_schema_marks_inadmissible")
    if record.availability_stage not in definition.allowed_stages or _STAGE_ORDER[record.availability_stage] > _STAGE_ORDER[task.prediction_stage]:
        return AdmissibilityResult(False, "feature_available_after_prediction_stage")
    if _is_prohibited(record):
        return AdmissibilityResult(False, "prohibited_source_field")
    if bool(record.provenance.get("target_leaking")) or bool(record.provenance.get("depends_on_target")) or bool(record.provenance.get("future_dependent")):
        return AdmissibilityResult(False, "provenance_indicates_target_or_future_dependency")
    return AdmissibilityResult(True)


def find_transport_duplicates(records: tuple[FeatureRecord, ...]) -> tuple[str, ...]:
    """Return stable warnings for direct/DRAA copies of the same declared source."""
    seen: set[tuple[str, str]] = set()
    warnings: list[str] = []
    for record in records:
        source_id = _source_identity(record)
        if source_id is None:
            continue
        key = (record.unit_id, source_id)
        direct_or_transport = record.source_namespace in {"draa", "layer1", "layer2", "bsda", "saea", "rc"}
        if key in seen and direct_or_transport:
            warnings.append(f"duplicate_direct_draa_evidence:{record.unit_id}:{source_id}")
        seen.add(key)
    return tuple(sorted(set(warnings)))


def deduplicate_transport_records(records: tuple[FeatureRecord, ...]) -> tuple[FeatureRecord, ...]:
    """Keep a direct source in preference to its DRAA transport copy."""
    selected: dict[tuple[str, str] | tuple[str, str, str], FeatureRecord] = {}
    for record in records:
        source_id = _source_identity(record)
        key: tuple[str, str] | tuple[str, str, str]
        key = (record.unit_id, source_id) if source_id is not None else (record.unit_id, record.source_namespace, record.feature_name)
        existing = selected.get(key)
        if existing is None or (existing.source_namespace == "draa" and record.source_namespace != "draa"):
            selected[key] = record
    return tuple(selected[key] for key in sorted(selected, key=str))


def _definition(schema: FeatureSchema, name: str) -> FeatureDefinition | None:
    return next((definition for definition in schema.features if definition.name == name), None)


def _is_prohibited(record: FeatureRecord) -> bool:
    field = str(record.provenance.get("source_field", record.feature_name))
    if record.source_namespace == "draa" and field == "risk_score":
        return True
    if record.source_namespace == "pri" and field in {"scalar_pri", "profile", "profile_cell", "profile_features"}:
        return True
    return record.source_namespace == "pri"


def _source_identity(record: FeatureRecord) -> str | None:
    """Use source-native provenance to identify a transported copy, if declared."""
    for key in ("source_result_id", "source_artifact_id", "artifact_id", "evaluation_id"):
        value = record.provenance.get(key)
        if isinstance(value, str):
            return value
    return record.source_artifact_id
