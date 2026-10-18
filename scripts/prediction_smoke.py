"""CPU-only Phase 9B smoke check using explicitly synthetic fixture labels."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.prediction.baselines import LogisticRegressionConfig
from core.prediction.models import (
    FeatureDefinition, FeatureRecord, FeatureSchema, HierarchyIdentifiers,
    LabelStatus, PredictionStage, PredictionTask, SemanticStatus, SplitPolicy,
    SplitStrategy, TargetRecord,
)
from core.prediction.splitting import build_grouped_manifest
from core.prediction.training import train_fixture_baselines


def main() -> None:
    task = PredictionTask("prediction-smoke", "synthetic_fixture_outcome", "synthetic-target-v1", "binary_classification", "evaluation_case", PredictionStage.POST_RESPONSE, "admissibility-v1", ("base_case_id",), label_status=LabelStatus.SYNTHETIC)
    schema = FeatureSchema("prediction-smoke-schema", "v1", task.task_id, (FeatureDefinition("signal", "numeric", "layer1", (PredictionStage.POST_RESPONSE,), "explicit_indicator"),))
    targets = tuple(TargetRecord("synthetic-target-v1", task.task_id, f"unit-{index}", index % 2, "binary", SemanticStatus.AVAILABLE, True, label_source="synthetic_fixture", hierarchy=HierarchyIdentifiers(base_case_id=f"case-{index}")) for index in range(12))
    features = tuple(FeatureRecord("v1", "signal", "layer1", target.unit_id, float(target.value), "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE, hierarchy=target.hierarchy) for target in targets)
    policy = SplitPolicy("prediction-smoke-policy", "v1", SplitStrategy.GROUPED_HOLDOUT, ("base_case_id",), ("train", "validation", "test"), {"train": 0.5, "validation": 0.25, "test": 0.25}, 17, "deterministic synthetic smoke fixture")
    manifest = build_grouped_manifest(manifest_id="prediction-smoke-manifest", policy=policy, target_schema_version="synthetic-target-v1", feature_schema=schema, targets=targets)
    result = train_fixture_baselines(experiment_id="prediction-smoke-experiment", task=task, schema=schema, features=features, targets=targets, manifest=manifest, logistic_config=LogisticRegressionConfig(200, 0.2, 0.1))
    if result.status != "trained" or result.experiment is None:
        raise RuntimeError(f"prediction smoke failed: {result.reason}")
    print({"service": "securellmbench", "phase": "9B", "mode": "engineering_baseline", "target_source": "synthetic", "scientific_status": result.experiment.scientific_status.value, "estimators": ["prevalence", "logistic_regression"], "calibration_status": "not_calibrated"})


if __name__ == "__main__":
    main()
