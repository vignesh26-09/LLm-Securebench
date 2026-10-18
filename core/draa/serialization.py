"""Deterministic JSON serialization for Mode A/B evidence records."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum

from core.draa.models import DRAAEvidenceRecord, DRAAMode, DRAAStatus, EvidenceFeature, SeverityEvidence, Uncertainty


def dumps(record: DRAAEvidenceRecord) -> str:
    return json.dumps(_ready(record), sort_keys=True, separators=(",", ":"))


def loads(payload: str) -> DRAAEvidenceRecord:
    value = json.loads(payload)
    features = tuple(_feature(item) for item in value["features"])
    severity = _severity(value.get("severity"))
    return DRAAEvidenceRecord(
        evaluation_id=value.get("evaluation_id"), case_id=value.get("case_id"), attack_id=value.get("attack_id"), run_id=value.get("run_id"), sequence_id=value.get("sequence_id"), model_id=value.get("model_id"), dataset_id=value.get("dataset_id"), dataset_version=value.get("dataset_version"), threat_model=value.get("threat_model"), mode=DRAAMode(value["mode"]), status=DRAAStatus(value["status"]), features=features, severity=severity, provenance=value.get("provenance", {}), warnings=tuple(value.get("warnings", ())), errors=tuple(value.get("errors", ())), schema_version=value["schema_version"], risk_score=value.get("risk_score"),
    )


def _feature(value: dict[str, object]) -> EvidenceFeature:
    uncertainty = _uncertainty(value.get("uncertainty"))
    return EvidenceFeature(namespace=str(value["namespace"]), name=str(value["name"]), raw_value=value.get("raw_value"), value_type=str(value["value_type"]), units=value.get("units"), orientation=value.get("orientation"), status=DRAAStatus(value["status"]), normalized_value=value.get("normalized_value"), status_reason=value.get("status_reason"), uncertainty=uncertainty, confidence=value.get("confidence"), provenance=value.get("provenance", {}), failure=value.get("failure"))


def _severity(value: object) -> SeverityEvidence | None:
    if value is None:
        return None
    data = dict(value)
    return SeverityEvidence(data.get("raw_value"), data.get("taxonomy_version"), data.get("source"), _uncertainty(data.get("uncertainty")), data.get("provenance", {}))


def _uncertainty(value: object) -> Uncertainty | None:
    if value is None:
        return None
    data = dict(value)
    return Uncertainty(tuple(data["confidence_interval"]) if data.get("confidence_interval") else None, data.get("standard_error"), tuple(data["bootstrap_interval"]) if data.get("bootstrap_interval") else None, data.get("reason"))


def _ready(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_ready(item) for item in value]
    return value
