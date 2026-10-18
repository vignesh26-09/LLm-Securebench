"""Phase 9B fixture baseline training service; it never derives labels upstream."""

from __future__ import annotations

import platform
from dataclasses import asdict, dataclass
from typing import Iterable

from core.prediction.admissibility import check_feature, deduplicate_transport_records, find_transport_duplicates
from core.prediction.artifacts import MLExperimentArtifact
from core.prediction.baselines import LogisticRegressionBaseline, LogisticRegressionConfig, PrevalenceBaseline
from core.prediction.metrics import MetricValue, evaluate_binary
from core.prediction.models import (
    EngineeringStatus, FeatureRecord, FeatureSchema, LabelStatus, PredictionTask,
    SemanticStatus, SplitManifest, TargetRecord, ValidationStatus,
)
from core.prediction.preprocessing import PreprocessingConfig, fit_preprocessor
from core.prediction.serialization import schema_hash


@dataclass(frozen=True, slots=True)
class TrainingResult:
    status: str
    reason: str | None
    prevalence_model: PrevalenceBaseline | None
    logistic_model: LogisticRegressionBaseline | None
    metrics: dict[str, dict[str, MetricValue]]
    experiment: MLExperimentArtifact | None


def train_fixture_baselines(*, experiment_id: str, task: PredictionTask, schema: FeatureSchema, features: Iterable[FeatureRecord], targets: Iterable[TargetRecord], manifest: SplitManifest, logistic_config: LogisticRegressionConfig, preprocessing_config: PreprocessingConfig = PreprocessingConfig()) -> TrainingResult:
    """Train only on explicit available fixture/external labels and train partition data."""
    if task.engineering_status is not EngineeringStatus.ENGINEERING_READY:
        return _blocked("task_not_engineering_ready")
    if task.label_status is LabelStatus.LABEL_BLOCKED:
        return _blocked("task_label_status_blocked")
    supplied_records = tuple(features)
    target_map = {item.unit_id: item for item in targets}
    warnings = list(find_transport_duplicates(supplied_records))
    records = deduplicate_transport_records(supplied_records)
    inadmissible = [check_feature(task, schema, record).reason for record in records if not check_feature(task, schema, record).accepted]
    if inadmissible:
        return _blocked(f"feature_admissibility_failed:{sorted(set(inadmissible))[0]}")
    if schema.prediction_task_id != task.task_id or manifest.feature_schema_hash != schema.schema_hash:
        return _blocked("schema_or_manifest_mismatch")
    if task.required_grouping and manifest.grouping_key not in task.required_grouping:
        return _blocked("required_task_grouping_unavailable")
    available = {unit: target for unit, target in target_map.items() if target.status is SemanticStatus.AVAILABLE and target.applicable}
    if not available:
        return _blocked("no_available_labels")
    try:
        labels = {unit: _binary_label(target.value) for unit, target in available.items()}
    except ValueError as error:
        return _blocked(str(error))
    if any(unit not in manifest.unit_partitions for unit in labels):
        return _blocked("label_missing_from_split_manifest")
    train_units = tuple(sorted(unit for unit in labels if manifest.unit_partitions[unit] == "train"))
    test_units = tuple(sorted(unit for unit in labels if manifest.unit_partitions[unit] == "test"))
    if not train_units or not test_units:
        return _blocked("train_and_test_partitions_required")
    training_records = tuple(record for record in records if record.unit_id in train_units)
    try:
        preprocessor = fit_preprocessor(schema, training_records, preprocessing_config)
        vectors = preprocessor.transform(record for record in records if record.unit_id in labels)
        train_rows = [vectors[unit] for unit in train_units]
        test_rows = [vectors[unit] for unit in test_units]
    except (ValueError, KeyError) as error:
        return _blocked(f"preprocessing_failed:{error}")
    train_labels = [labels[unit] for unit in train_units]
    test_labels = [labels[unit] for unit in test_units]
    prevalence = PrevalenceBaseline.fit(train_labels)
    if len(set(train_labels)) < 2:
        return _blocked("logistic_regression_requires_two_training_classes", prevalence=prevalence)
    logistic = LogisticRegressionBaseline.fit(train_rows, train_labels, logistic_config)
    prevalence_scores = [output.raw_score for output in prevalence.predict(test_rows)]
    logistic_scores = [output.raw_score for output in logistic.predict(test_rows)]
    metrics = {"prevalence": evaluate_binary(test_labels, prevalence_scores), "logistic_regression": evaluate_binary(test_labels, logistic_scores)}
    synthetic = task.label_status is LabelStatus.SYNTHETIC or all(target.label_source == "synthetic_fixture" for target in available.values())
    status = ValidationStatus.ENGINEERING_BASELINE_ONLY if synthetic else ValidationStatus.NOT_VALIDATED
    artifact = MLExperimentArtifact(experiment_id, task.task_id, task.target_schema_version, task.target_schema_version, schema.version, schema.schema_hash, task.prediction_stage.value, manifest.manifest_id, schema_hash(manifest), manifest.grouping_key or "", asdict(preprocessing_config), "phase9b_baselines", {"logistic_regression": asdict(logistic_config), "prevalence": {"training_labels_only": True}}, manifest.seed, {"python": platform.python_version()}, metrics["logistic_regression"], dict(manifest.benchmark_identity), dict(manifest.dataset_identity), {}, {"sources": sorted({target.label_source for target in available.values() if target.label_source})}, synthetic, status, tuple(warnings))
    return TrainingResult("trained", None, prevalence, logistic, metrics, artifact)


def _binary_label(value: object | None) -> int:
    if value in (0, 1) and not isinstance(value, bool):
        return int(value)
    raise ValueError("available target values must be explicit binary integer labels")


def _blocked(reason: str, prevalence: PrevalenceBaseline | None = None) -> TrainingResult:
    return TrainingResult("blocked", reason, prevalence, None, {}, None)
