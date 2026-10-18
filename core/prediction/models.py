"""Phase 9 prediction contracts; schemas do not assert scientific validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum, StrEnum
from typing import Mapping


class PredictionStage(StrEnum):
    PRE_PROMPT_STATIC = "pre_prompt_static"
    PRE_GENERATION = "pre_generation"
    POST_RESPONSE = "post_response"
    HISTORICAL_SESSION = "historical_session"
    POST_SESSION = "post_session"
    MODEL_LEVEL_HISTORICAL = "model_level_historical"


class SemanticStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    NOT_EVALUATED = "not_evaluated"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"
    UNDEFINED = "undefined"
    INSUFFICIENT_DATA = "insufficient_data"
    UNAVAILABLE = "unavailable"
    UNCALIBRATED = "uncalibrated"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"


class EngineeringStatus(StrEnum):
    ENGINEERING_READY = "engineering_ready"
    ENGINEERING_BLOCKED = "engineering_blocked"


class LabelStatus(StrEnum):
    LABEL_READY = "label_ready"
    LABEL_DEPENDENT = "label_dependent"
    LABEL_BLOCKED = "label_blocked"
    SYNTHETIC = "synthetic"


class ValidationStatus(StrEnum):
    NOT_VALIDATED = "not_validated"
    ENGINEERING_BASELINE_ONLY = "engineering_baseline_only"
    EMPIRICALLY_VALIDATED = "empirically_validated"


class CalibrationStatus(StrEnum):
    NOT_CALIBRATED = "not_calibrated"


class SplitStrategy(StrEnum):
    GROUPED_HOLDOUT = "grouped_holdout"
    DIAGNOSTIC_LEAKAGE_BASELINE = "diagnostic_leakage_baseline"


@dataclass(frozen=True, slots=True)
class HierarchyIdentifiers:
    """Optional hierarchy only; absent identifiers are never fabricated."""

    model_configuration_id: str | None = None
    benchmark_id: str | None = None
    dataset_id: str | None = None
    category: str | None = None
    attack_family_id: str | None = None
    base_case_id: str | None = None
    prompt_variant_id: str | None = None
    stochastic_run_id: str | None = None
    session_id: str | None = None
    sequence_id: str | None = None
    turn_id: str | None = None


@dataclass(frozen=True, slots=True)
class PredictionTask:
    task_id: str
    target_name: str
    target_schema_version: str
    task_type: str
    prediction_unit: str
    prediction_stage: PredictionStage
    admissibility_policy_version: str
    required_grouping: tuple[str, ...] = ()
    benchmark_context: Mapping[str, object] = field(default_factory=dict)
    threat_context: Mapping[str, object] = field(default_factory=dict)
    provenance: Mapping[str, object] = field(default_factory=dict)
    engineering_status: EngineeringStatus = EngineeringStatus.ENGINEERING_READY
    label_status: LabelStatus = LabelStatus.LABEL_DEPENDENT
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED

    def __post_init__(self) -> None:
        if not all((self.task_id, self.target_name, self.target_schema_version, self.task_type, self.prediction_unit, self.admissibility_policy_version)):
            raise ValueError("prediction task requires identity, target, type, unit, and policy version")


@dataclass(frozen=True, slots=True)
class TargetRecord:
    target_schema_version: str
    prediction_task_id: str
    unit_id: str
    value: object | None
    value_type: str
    status: SemanticStatus
    applicable: bool
    reason: str | None = None
    label_source: str | None = None
    evidence_provenance: Mapping[str, object] = field(default_factory=dict)
    label_timestamp: str | None = None
    hierarchy: HierarchyIdentifiers = field(default_factory=HierarchyIdentifiers)
    source_artifact_id: str | None = None
    source_artifact_version: str | None = None

    def __post_init__(self) -> None:
        if not all((self.target_schema_version, self.prediction_task_id, self.unit_id, self.value_type)):
            raise ValueError("target record requires schema, task, unit, and value type")
        if self.status is not SemanticStatus.AVAILABLE and self.value is not None:
            raise ValueError("a semantic non-value status must not carry a target value")
        if self.status is SemanticStatus.AVAILABLE and not self.applicable:
            raise ValueError("an available target must be applicable")


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    name: str
    expected_type: str
    source_namespace: str
    allowed_stages: tuple[PredictionStage, ...]
    semantic_missingness_policy: str
    preprocessing: Mapping[str, object] = field(default_factory=dict)
    admissible: bool = True
    admissibility_reason: str | None = None

    def __post_init__(self) -> None:
        if not all((self.name, self.expected_type, self.source_namespace, self.semantic_missingness_policy)):
            raise ValueError("feature definition requires name, type, namespace, and missingness policy")
        if not self.allowed_stages:
            raise ValueError("feature definition requires one or more allowed stages")


@dataclass(frozen=True, slots=True)
class FeatureSchema:
    schema_id: str
    version: str
    prediction_task_id: str
    features: tuple[FeatureDefinition, ...]

    def __post_init__(self) -> None:
        if not all((self.schema_id, self.version, self.prediction_task_id)):
            raise ValueError("feature schema requires identity and task ID")
        names = tuple(item.name for item in self.features)
        if len(names) != len(set(names)):
            raise ValueError("feature schema feature names must be unique")
        if names != tuple(sorted(names)):
            raise ValueError("feature schema features must be deterministically name-sorted")

    @property
    def schema_hash(self) -> str:
        payload = json.dumps(_json_ready(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FeatureRecord:
    feature_schema_version: str
    feature_name: str
    source_namespace: str
    unit_id: str
    raw_value: object | None
    value_type: str
    status: SemanticStatus
    availability_stage: PredictionStage
    source_artifact_id: str | None = None
    source_artifact_version: str | None = None
    units: str | None = None
    orientation: str | None = None
    reason: str | None = None
    extraction_timestamp: str | None = None
    hierarchy: HierarchyIdentifiers = field(default_factory=HierarchyIdentifiers)
    uncertainty: Mapping[str, object] | None = None
    confidence: float | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.feature_schema_version, self.feature_name, self.source_namespace, self.unit_id, self.value_type)):
            raise ValueError("feature record requires schema, feature, namespace, unit, and value type")
        if self.status is not SemanticStatus.AVAILABLE and self.raw_value is not None:
            raise ValueError("a semantic non-value status must not carry a raw value")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("feature confidence must be in [0, 1]")
        json.dumps(self.raw_value)


@dataclass(frozen=True, slots=True)
class SplitPolicy:
    policy_id: str
    version: str
    strategy: SplitStrategy
    grouping_keys: tuple[str, ...]
    requested_partitions: tuple[str, ...]
    partition_fractions: Mapping[str, float] | None = None
    seed: int | None = None
    rationale: str = ""
    intent: str = "scientific_style"

    def __post_init__(self) -> None:
        if not all((self.policy_id, self.version)) or not self.requested_partitions:
            raise ValueError("split policy requires identity and partitions")
        if self.strategy is SplitStrategy.GROUPED_HOLDOUT and not self.grouping_keys:
            raise ValueError("grouped holdout requires one or more grouping keys")
        if len(self.requested_partitions) != len(set(self.requested_partitions)):
            raise ValueError("split partitions must be unique")
        if self.partition_fractions is not None:
            if set(self.partition_fractions) != set(self.requested_partitions):
                raise ValueError("partition fractions must name exactly the requested partitions")
            if any(value < 0 for value in self.partition_fractions.values()) or sum(self.partition_fractions.values()) <= 0:
                raise ValueError("partition fractions must be non-negative with positive total")


@dataclass(frozen=True, slots=True)
class SplitManifest:
    manifest_id: str
    policy_id: str
    policy_version: str
    target_schema_version: str
    feature_schema_version: str
    feature_schema_hash: str
    grouping_key: str | None
    unit_partitions: Mapping[str, str]
    group_partitions: Mapping[str, str]
    seed: int | None
    dataset_identity: Mapping[str, object] = field(default_factory=dict)
    benchmark_identity: Mapping[str, object] = field(default_factory=dict)
    provenance: Mapping[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.manifest_id, self.policy_id, self.policy_version, self.target_schema_version, self.feature_schema_version, self.feature_schema_hash)):
            raise ValueError("split manifest requires identity and schema provenance")
        valid = set(self.group_partitions.values())
        if any(partition not in valid for partition in self.unit_partitions.values()):
            raise ValueError("all unit partitions must be represented by group assignments")


def _json_ready(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value
