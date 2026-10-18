"""Machine-readable metadata artifacts; fitted Python objects are not persisted here."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from core.prediction.metrics import MetricValue
from core.prediction.models import CalibrationStatus, ValidationStatus


@dataclass(frozen=True, slots=True)
class MLExperimentArtifact:
    experiment_id: str
    task_id: str
    task_schema_version: str
    target_schema_version: str
    feature_schema_version: str
    feature_schema_hash: str
    prediction_stage: str
    split_manifest_id: str
    split_manifest_hash: str
    grouping_strategy: str
    preprocessing_configuration: Mapping[str, object]
    estimator_family: str
    estimator_configuration: Mapping[str, object]
    effective_seed: int | None
    software_versions: Mapping[str, str]
    metrics: Mapping[str, MetricValue] = field(default_factory=dict)
    benchmark_identity: Mapping[str, object] = field(default_factory=dict)
    dataset_identity: Mapping[str, object] = field(default_factory=dict)
    model_population: Mapping[str, object] = field(default_factory=dict)
    label_provenance: Mapping[str, object] = field(default_factory=dict)
    synthetic_labels: bool = False
    scientific_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.experiment_id, self.task_id, self.task_schema_version, self.target_schema_version, self.feature_schema_version, self.feature_schema_hash, self.split_manifest_id, self.split_manifest_hash, self.estimator_family)):
            raise ValueError("experiment artifact requires identities, schema provenance, split, and estimator")
        if self.synthetic_labels and self.scientific_status is not ValidationStatus.ENGINEERING_BASELINE_ONLY:
            raise ValueError("synthetic labels require engineering_baseline_only status")


@dataclass(frozen=True, slots=True)
class MLModelArtifact:
    artifact_id: str
    experiment_id: str
    estimator_family: str
    estimator_configuration: Mapping[str, object]
    preprocessing_configuration: Mapping[str, object]
    feature_schema_hash: str
    target_schema_version: str
    split_manifest_hash: str
    training_population_identity: Mapping[str, object]
    raw_output_semantics: str
    calibration_status: CalibrationStatus
    serialization_format: str | None = None
    artifact_hash: str | None = None
    dependency_versions: Mapping[str, str] = field(default_factory=dict)
    trusted_provenance_required: bool = True
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.artifact_id, self.experiment_id, self.estimator_family, self.feature_schema_hash, self.target_schema_version, self.split_manifest_hash, self.raw_output_semantics)):
            raise ValueError("model artifact metadata requires identity, schemas, split, and output semantics")
