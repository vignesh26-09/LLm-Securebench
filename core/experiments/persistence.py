"""Append-only persistence adapter for scientific experiment artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Mapping

from core.persistence.models import ScientificRecordEntity
from core.persistence.repositories import ScientificRecordRepository


ALLOWED_FAMILIES = frozenset({
    "experiment_specification", "experimental_condition", "conversation",
    "control_match_identity", "attack_outcome", "judge_calibration",
    "bsda", "recovery", "saea", "paired_analysis", "complementarity",
    "reproducibility_manifest", "preregistration", "analysis_plan_diff",
    "session_contamination", "replication_bundle", "replication_replay",
})


def append_scientific_artifact(session, *, record_id: str, family: str,
                               schema_version: str, scope: str, owner_id: str | None,
                               status: str | None, artifact: object,
                               provenance: Mapping[str, object] | None = None) -> ScientificRecordEntity:
    if family not in ALLOWED_FAMILIES:
        raise ValueError(f"unsupported scientific artifact family: {family}")
    repository = ScientificRecordRepository(session)
    if repository.get(record_id) is not None:
        raise ValueError(f"immutable scientific artifact already exists: {record_id}")
    payload = _json_value(asdict(artifact) if is_dataclass(artifact) else artifact)
    record = ScientificRecordEntity(
        id=record_id, family=family, schema_version=schema_version, scope=scope,
        owner_id=owner_id, status=status, payload=payload,
        provenance=_json_value(dict(provenance or {})),
    )
    repository.add(record)
    session.commit()
    return record


def _json_value(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.loads(json.dumps(value, default=str))
