"""Deterministic Phase 9A/B tests using synthetic labels only."""

import unittest

from core.prediction.admissibility import check_feature, deduplicate_transport_records, find_transport_duplicates
from core.prediction.artifacts import MLExperimentArtifact, MLModelArtifact
from core.prediction.baselines import CalibrationStatus, LogisticRegressionConfig
from core.prediction.metrics import evaluate_binary
from core.prediction.models import (
    EngineeringStatus, FeatureDefinition, FeatureRecord, FeatureSchema,
    HierarchyIdentifiers, LabelStatus, PredictionStage, PredictionTask,
    SemanticStatus, SplitManifest, SplitPolicy, SplitStrategy, TargetRecord,
    ValidationStatus,
)
from core.prediction.preprocessing import fit_preprocessor
from core.prediction.serialization import (
    dumps, loads_experiment, loads_feature_record, loads_feature_schema,
    loads_model_artifact, loads_prediction_task, loads_split_manifest,
    loads_split_policy, loads_target_record,
)
from core.prediction.splitting import build_grouped_manifest
from core.prediction.training import train_fixture_baselines


class PredictionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = PredictionTask("synthetic-binary", "fixture_outcome", "target-v1", "binary_classification", "evaluation_case", PredictionStage.POST_RESPONSE, "admissibility-v1", ("base_case_id",), label_status=LabelStatus.SYNTHETIC)
        self.schema = FeatureSchema("fixture-features", "feature-v1", self.task.task_id, (FeatureDefinition("category", "categorical", "dataset", (PredictionStage.PRE_PROMPT_STATIC,), "explicit_indicator"), FeatureDefinition("signal", "numeric", "layer1", (PredictionStage.POST_RESPONSE,), "explicit_indicator")))
        self.targets = tuple(TargetRecord("target-v1", self.task.task_id, f"u{index}", index % 2, "binary", SemanticStatus.AVAILABLE, True, label_source="synthetic_fixture", hierarchy=HierarchyIdentifiers(base_case_id=f"g{index}")) for index in range(8))
        self.features = tuple(record for index in range(8) for record in (FeatureRecord("feature-v1", "category", "dataset", f"u{index}", "even" if index % 2 == 0 else "odd", "categorical", SemanticStatus.AVAILABLE, PredictionStage.PRE_PROMPT_STATIC, hierarchy=HierarchyIdentifiers(base_case_id=f"g{index}")), FeatureRecord("feature-v1", "signal", "layer1", f"u{index}", float(index % 2), "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE, hierarchy=HierarchyIdentifiers(base_case_id=f"g{index}"))))
        self.policy = SplitPolicy("fixture-grouped", "v1", SplitStrategy.GROUPED_HOLDOUT, ("base_case_id",), ("train", "validation", "test"), {"train": 0.5, "validation": 0.25, "test": 0.25}, 7, "synthetic grouped fixture")
        self.manifest = build_grouped_manifest(manifest_id="manifest-1", policy=self.policy, target_schema_version="target-v1", feature_schema=self.schema, targets=self.targets)

    def test_round_trips_and_deterministic_schema_hash(self) -> None:
        self.assertEqual(loads_prediction_task(dumps(self.task)), self.task)
        self.assertEqual(loads_feature_schema(dumps(self.schema)), self.schema)
        self.assertEqual(loads_feature_record(dumps(self.features[0])), self.features[0])
        self.assertEqual(loads_target_record(dumps(self.targets[0])), self.targets[0])
        self.assertEqual(loads_split_policy(dumps(self.policy)), self.policy)
        self.assertEqual(loads_split_manifest(dumps(self.manifest)), self.manifest)
        self.assertEqual(self.schema.schema_hash, FeatureSchema("fixture-features", "feature-v1", self.task.task_id, self.schema.features).schema_hash)

    def test_readiness_states_are_separate(self) -> None:
        task = PredictionTask("t", "x", "v", "binary", "case", PredictionStage.PRE_GENERATION, "v", engineering_status=EngineeringStatus.ENGINEERING_READY, label_status=LabelStatus.LABEL_DEPENDENT, validation_status=ValidationStatus.NOT_VALIDATED)
        self.assertIs(task.engineering_status, EngineeringStatus.ENGINEERING_READY)
        self.assertIs(task.label_status, LabelStatus.LABEL_DEPENDENT)
        self.assertIs(task.validation_status, ValidationStatus.NOT_VALIDATED)

    def test_admissibility_rejects_future_leaks_draa_and_pri(self) -> None:
        future = FeatureRecord("feature-v1", "signal", "layer1", "u0", 0.2, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_SESSION)
        self.assertFalse(check_feature(self.task, self.schema, future).accepted)
        leak = FeatureRecord("feature-v1", "signal", "layer1", "u0", 0.2, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE, provenance={"target_leaking": True})
        self.assertFalse(check_feature(self.task, self.schema, leak).accepted)
        draa_schema = FeatureSchema("d", "v", self.task.task_id, (FeatureDefinition("risk_score", "numeric", "draa", (PredictionStage.POST_RESPONSE,), "indicator"),))
        draa = FeatureRecord("v", "risk_score", "draa", "u0", 0.3, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE, provenance={"source_field": "risk_score"})
        self.assertFalse(check_feature(self.task, draa_schema, draa).accepted)
        pri_schema = FeatureSchema("p", "v", self.task.task_id, (FeatureDefinition("scalar_pri", "numeric", "pri", (PredictionStage.POST_RESPONSE,), "indicator"),))
        pri = FeatureRecord("v", "scalar_pri", "pri", "u0", 0.3, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE)
        self.assertFalse(check_feature(self.task, pri_schema, pri).accepted)

    def test_draa_transport_duplicate_is_warned(self) -> None:
        direct = FeatureRecord("feature-v1", "signal", "layer1", "u0", 0.2, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE, provenance={"source_result_id": "source-1"})
        transport = FeatureRecord("feature-v1", "signal_transport", "draa", "u0", 0.2, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE, provenance={"source_result_id": "source-1"})
        self.assertTrue(find_transport_duplicates((direct, transport)))
        self.assertEqual(deduplicate_transport_records((transport, direct)), (direct,))

    def test_grouped_manifest_is_deterministic_and_keeps_groups_together(self) -> None:
        repeated = self.targets + (TargetRecord("target-v1", self.task.task_id, "u0-repeat", 0, "binary", SemanticStatus.AVAILABLE, True, label_source="synthetic_fixture", hierarchy=HierarchyIdentifiers(base_case_id="g0", stochastic_run_id="run-2")),)
        first = build_grouped_manifest(manifest_id="m", policy=self.policy, target_schema_version="target-v1", feature_schema=self.schema, targets=repeated)
        second = build_grouped_manifest(manifest_id="m", policy=self.policy, target_schema_version="target-v1", feature_schema=self.schema, targets=repeated)
        self.assertEqual(first, second)
        self.assertEqual(first.unit_partitions["u0"], first.unit_partitions["u0-repeat"])
        changed = build_grouped_manifest(manifest_id="m", policy=SplitPolicy("p", "v", SplitStrategy.GROUPED_HOLDOUT, ("base_case_id",), ("train", "validation", "test"), {"train": .5, "validation": .25, "test": .25}, 8), target_schema_version="target-v1", feature_schema=self.schema, targets=self.targets)
        self.assertNotEqual(first.group_partitions, changed.group_partitions)

    def test_preprocessor_is_training_only_and_retains_missingness(self) -> None:
        train = (FeatureRecord("feature-v1", "signal", "layer1", "train", 2.0, "numeric", SemanticStatus.AVAILABLE, PredictionStage.POST_RESPONSE), FeatureRecord("feature-v1", "category", "dataset", "train", "seen", "categorical", SemanticStatus.AVAILABLE, PredictionStage.PRE_PROMPT_STATIC))
        fitted = fit_preprocessor(self.schema, train)
        self.assertEqual(fitted.numeric_means["signal"], 2.0)
        unknown = (FeatureRecord("feature-v1", "signal", "layer1", "test", None, "numeric", SemanticStatus.MISSING, PredictionStage.POST_RESPONSE), FeatureRecord("feature-v1", "category", "dataset", "test", "new", "categorical", SemanticStatus.AVAILABLE, PredictionStage.PRE_PROMPT_STATIC))
        row = fitted.transform(unknown)["test"]
        self.assertEqual(row[1], 1.0)
        self.assertIn("category=__unknown__", fitted.output_names)

    def test_baselines_train_only_on_synthetic_fixture_and_are_not_calibrated(self) -> None:
        result = train_fixture_baselines(experiment_id="exp", task=self.task, schema=self.schema, features=self.features, targets=self.targets, manifest=self.manifest, logistic_config=LogisticRegressionConfig(150, 0.2, 0.1))
        self.assertEqual(result.status, "trained")
        self.assertIsNotNone(result.logistic_model)
        self.assertIs(result.experiment.scientific_status, ValidationStatus.ENGINEERING_BASELINE_ONLY)
        output = result.logistic_model.predict(((0.0, 0.0, 0.0, 1.0, 0.0),))[0]
        self.assertIs(output.calibration_status, CalibrationStatus.NOT_CALIBRATED)
        self.assertIn("roc_auc", result.metrics["logistic_regression"])

    def test_blocked_and_one_class_training_are_explicit(self) -> None:
        blocked_task = PredictionTask("b", "x", "v", "binary", "case", PredictionStage.POST_RESPONSE, "v", label_status=LabelStatus.LABEL_BLOCKED)
        result = train_fixture_baselines(experiment_id="x", task=blocked_task, schema=self.schema, features=self.features, targets=self.targets, manifest=self.manifest, logistic_config=LogisticRegressionConfig(10, .1, .1))
        self.assertEqual(result.status, "blocked")
        one_class = tuple(TargetRecord("target-v1", self.task.task_id, target.unit_id, 1, "binary", SemanticStatus.AVAILABLE, True, label_source="synthetic_fixture", hierarchy=target.hierarchy) for target in self.targets)
        result = train_fixture_baselines(experiment_id="x", task=self.task, schema=self.schema, features=self.features, targets=one_class, manifest=self.manifest, logistic_config=LogisticRegressionConfig(10, .1, .1))
        self.assertEqual(result.reason, "logistic_regression_requires_two_training_classes")

    def test_metrics_threshold_and_one_class_states(self) -> None:
        metrics = evaluate_binary((0, 1, 0, 1), (.1, .9, .2, .8))
        self.assertEqual(metrics["roc_auc"].value, 1.0)
        self.assertEqual(metrics["precision"].status, "not_computed")
        thresholded = evaluate_binary((0, 1, 0, 1), (.1, .9, .2, .8), threshold=.5)
        self.assertEqual(thresholded["f1"].value, 1.0)
        self.assertEqual(evaluate_binary((1, 1), (.3, .4))["roc_auc"].status, "undefined")

    def test_artifact_round_trips(self) -> None:
        experiment = MLExperimentArtifact("e", self.task.task_id, "target-v1", "target-v1", "feature-v1", self.schema.schema_hash, "post_response", "m", "hash", "base_case_id", {}, "prevalence", {}, 1, {"python": "3.11"}, synthetic_labels=True, scientific_status=ValidationStatus.ENGINEERING_BASELINE_ONLY)
        self.assertEqual(loads_experiment(dumps(experiment)), experiment)
        model = MLModelArtifact("model", "e", "logistic_regression", {}, {}, self.schema.schema_hash, "target-v1", "hash", {}, "uncalibrated model probability estimate", CalibrationStatus.NOT_CALIBRATED)
        self.assertEqual(loads_model_artifact(dumps(model)), model)


if __name__ == "__main__":
    unittest.main()
