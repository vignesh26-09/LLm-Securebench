"""Immutable DRAA evidence contracts without aggregation or prediction."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


DRAA_SCHEMA_VERSION = "draa-evidence-v1"


class DRAAMode(StrEnum):
    FEATURE_EXTRACTION = "mode_a_feature_extraction"
    UNCALIBRATED_DIAGNOSTICS = "mode_b_uncalibrated_diagnostics"


class DRAAStatus(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNCALIBRATED = "uncalibrated"
    UNDEFINED = "undefined"
    FAILED = "failed"
    SKIPPED = "skipped"
    REFUSED = "refused"
    INSUFFICIENT_DATA = "insufficient_data"
    INCOMPATIBLE = "incompatible"
    ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class Uncertainty:
    confidence_interval: tuple[float, float] | None = None
    standard_error: float | None = None
    bootstrap_interval: tuple[float, float] | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceFeature:
    namespace: str
    name: str
    raw_value: object | None
    value_type: str
    units: str | None
    orientation: str | None
    status: DRAAStatus
    normalized_value: object | None = None
    status_reason: str | None = None
    uncertainty: Uncertainty | None = None
    confidence: float | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)
    failure: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not self.namespace or not self.name or not self.value_type:
            raise ValueError("evidence features require namespace, name, and value_type")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        # Detect non-machine-readable values early; absence is represented explicitly.
        json.dumps(self.raw_value)
        json.dumps(self.normalized_value)


@dataclass(frozen=True, slots=True)
class SeverityEvidence:
    raw_value: object | None
    taxonomy_version: str | None = None
    source: str | None = None
    uncertainty: Uncertainty | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DRAAEvidenceRecord:
    evaluation_id: str | None
    case_id: str | None
    attack_id: str | None
    run_id: str | None
    sequence_id: str | None
    model_id: str | None
    dataset_id: str | None
    dataset_version: str | None
    threat_model: str | None
    mode: DRAAMode
    status: DRAAStatus = DRAAStatus.UNCALIBRATED
    features: tuple[EvidenceFeature, ...] = ()
    severity: SeverityEvidence | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    schema_version: str = DRAA_SCHEMA_VERSION
    risk_score: None = None

    def __post_init__(self) -> None:
        if self.status is not DRAAStatus.UNCALIBRATED:
            raise ValueError("DRAA Mode A/B evidence records must be uncalibrated")
        if self.risk_score is not None:
            raise ValueError("DRAA Mode A/B must not contain a scalar risk score")


@dataclass(frozen=True, slots=True)
class DRAACalibrationArtifact:
    """Future Mode C data contract only; it does not fit or apply a predictor."""
    artifact_id: str
    methodology_version: str
    model_version: str
    label_definition_version: str
    upstream_versions: Mapping[str, str]
    selected_features: tuple[str, ...]
    feature_contracts: Mapping[str, Mapping[str, object]]
    reference_population: Mapping[str, object]
    model_parameters: Mapping[str, object]
    calibration_method: str | None
    missingness_policy: str | None
    dependence_policy: str | None
    uncertainty_policy: str | None
    coverage: Mapping[str, object]
    split_provenance: Mapping[str, object]
    validation_status: str
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.artifact_id, self.methodology_version, self.model_version, self.label_definition_version, self.validation_status)):
            raise ValueError("calibration artifact requires identity, label version, and validation status")
