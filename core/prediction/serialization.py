"""Deterministic JSON serialization for Phase 9 schemas and metadata."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import TypeVar

from core.prediction.artifacts import MLExperimentArtifact, MLModelArtifact
from core.prediction.metrics import MetricValue
from core.prediction.models import (
    CalibrationStatus, EngineeringStatus, FeatureDefinition, FeatureRecord,
    FeatureSchema, HierarchyIdentifiers, LabelStatus, PredictionStage,
    PredictionTask, SemanticStatus, SplitManifest, SplitPolicy, SplitStrategy,
    TargetRecord, ValidationStatus,
)

T = TypeVar("T")


def dumps(value: object) -> str:
    return json.dumps(_ready(value), sort_keys=True, separators=(",", ":"))


def schema_hash(value: object) -> str:
    import hashlib
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()


def loads_prediction_task(payload: str) -> PredictionTask:
    data = json.loads(payload)
    data["prediction_stage"] = PredictionStage(data["prediction_stage"])
    data["required_grouping"] = tuple(data.get("required_grouping", ()))
    data["engineering_status"] = EngineeringStatus(data["engineering_status"])
    data["label_status"] = LabelStatus(data["label_status"])
    data["validation_status"] = ValidationStatus(data["validation_status"])
    return PredictionTask(**data)


def loads_feature_schema(payload: str) -> FeatureSchema:
    data = json.loads(payload)
    data["features"] = tuple(FeatureDefinition(name=item["name"], expected_type=item["expected_type"], source_namespace=item["source_namespace"], allowed_stages=tuple(PredictionStage(stage) for stage in item["allowed_stages"]), semantic_missingness_policy=item["semantic_missingness_policy"], preprocessing=item.get("preprocessing", {}), admissible=item.get("admissible", True), admissibility_reason=item.get("admissibility_reason")) for item in data["features"])
    return FeatureSchema(**data)


def loads_feature_record(payload: str) -> FeatureRecord:
    data = json.loads(payload)
    data["status"] = SemanticStatus(data["status"])
    data["availability_stage"] = PredictionStage(data["availability_stage"])
    data["hierarchy"] = HierarchyIdentifiers(**data.get("hierarchy", {}))
    return FeatureRecord(**data)


def loads_target_record(payload: str) -> TargetRecord:
    data = json.loads(payload)
    data["status"] = SemanticStatus(data["status"])
    data["hierarchy"] = HierarchyIdentifiers(**data.get("hierarchy", {}))
    return TargetRecord(**data)


def loads_split_policy(payload: str) -> SplitPolicy:
    data = json.loads(payload)
    data["strategy"] = SplitStrategy(data["strategy"])
    data["grouping_keys"] = tuple(data.get("grouping_keys", ()))
    data["requested_partitions"] = tuple(data["requested_partitions"])
    return SplitPolicy(**data)


def loads_split_manifest(payload: str) -> SplitManifest:
    data = json.loads(payload)
    data["warnings"] = tuple(data.get("warnings", ()))
    return SplitManifest(**data)


def loads_experiment(payload: str) -> MLExperimentArtifact:
    data = json.loads(payload)
    data["scientific_status"] = ValidationStatus(data["scientific_status"])
    data["metrics"] = {key: MetricValue(**value) for key, value in data.get("metrics", {}).items()}
    data["warnings"] = tuple(data.get("warnings", ()))
    data["errors"] = tuple(data.get("errors", ()))
    return MLExperimentArtifact(**data)


def loads_model_artifact(payload: str) -> MLModelArtifact:
    data = json.loads(payload)
    data["calibration_status"] = CalibrationStatus(data["calibration_status"])
    return MLModelArtifact(**data)


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
