import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from sqlalchemy.orm import Session

from core.benchmark.engine import BenchmarkEngine
from core.benchmark.models import BenchmarkConfig
from core.benchmark.storage import JsonBenchmarkStore
from core.dataset.models import Dataset, DatasetRecord
from core.dataset.quality import calculate_dqi
from core.evaluation import (AttackOutcomeStatus, JudgeCalibrationPair,
    build_judge_calibration_artifact, calculate_asr, import_human_outcomes)
from core.experiments.manifest import stable_hash
from core.experiments.manifest import build_manifest
from core.experiments.models import (AttackDefinition, ControlMatchIdentity,
    EvaluationCaseDesign, ExperimentSpecification, MeasurementConfiguration,
    ExperimentalCondition, validate_control_match)
from core.experiments.persistence import append_scientific_artifact
from core.experiments.runner import ExperimentRunner, ObservationStore
from core.experiments.trajectory import (BehaviorMeasurement, build_recovery_input,
    build_saea_input)
from core.inference import GenerationConfig
from core.inference import ContextValidity
from core.inference.mock import MockInferenceProvider
from core.models.registry import InMemoryModelRegistry, ModelMetadata
from core.persistence.database import Base, make_engine
from core.saea.engine import SAEAEngine
from core.saea.models import (AttackInstance, BehavioralState, ContextStatus,
    ResultStatus, SAEAInput, SpacingCondition)
from core.statistics.complementarity import ComplementarityRow, complementarity_table
from core.statistics.paired import PairedValue, paired_difference_analysis
from core.recovery import RCCalibrationArtifact, RecoveryCapabilityEngine


def identity(**changes):
    values = dict(evaluation_case_id="case", attack_id="attack",
        attack_instance_id="attack-1", target_model="model", target_model_version="digest",
        provider="mock", generation_digest="generation", dataset_version="dataset-v1",
        behavior_representation_version="behavior-v1", layer1_version="layer1-v1",
        layer2_judge_version="judge-v1", measurement_version="measurement-v1",
        threat_model="injection")
    values.update(changes)
    return ControlMatchIdentity(**values)


def specification():
    return ExperimentSpecification(
        "experiment", "dataset", "dataset-v1", "sha256",
        (ModelMetadata("model", "mock", "digest", context_window=4096),),
        (EvaluationCaseDesign("case", "baseline",
            (AttackDefinition("a1", "attack-1", "injection", "attack one"),
             AttackDefinition("a2", "attack-2", "injection", "attack two")),
            (("attack-1", "attack-2"),), ("recover one", "recover two")),),
        GenerationConfig(temperature=0, max_new_tokens=16), (17,), 1,
        MeasurementConfiguration("behavior-v1", "layer1-v1", "judge-v1",
                                 "prompt-v1", "rubric-v1", "measurement-v1", "injection"))


class ControlledExperimentTests(unittest.TestCase):
    def test_stateful_sequence_isolated_controls_recovery_and_resume(self):
        provider = MockInferenceProvider(default_response="assistant")
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(Path(directory))
            observations = ExperimentRunner(provider, store).run(specification())
            sequential = [item for item in observations if item.condition is ExperimentalCondition.SEQUENTIAL_ATTACK]
            isolated = [item for item in observations if item.condition is ExperimentalCondition.ISOLATED_ATTACK]
            recovery = [item for item in observations if item.condition is ExperimentalCondition.RECOVERY]
            self.assertEqual([item.attack_instance_id for item in isolated], ["attack-1", "attack-2"])
            self.assertEqual([item.sequence_position for item in sequential], [1, 2])
            self.assertEqual(len(sequential[0].ordered_messages), 4)
            self.assertEqual(len(sequential[1].ordered_messages), 6)
            self.assertEqual(len(recovery[0].ordered_messages), 8)
            self.assertIn("attack two", [item["content"] for item in recovery[0].ordered_messages])
            self.assertNotIn("attack one", [item["content"] for item in isolated[1].ordered_messages])
            self.assertTrue(all(item.provider_supports_seed and item.effective_seed == 17 for item in observations))
            calls = len(provider.conversation_requests)
            repeated = ExperimentRunner(provider, store).run(specification())
            self.assertEqual(len(provider.conversation_requests), calls)
            self.assertEqual([item.observation_id for item in observations], [item.observation_id for item in repeated])

    def test_mock_history_reaches_each_turn(self):
        provider = MockInferenceProvider(default_response="answer")
        with tempfile.TemporaryDirectory() as directory:
            ExperimentRunner(provider, ObservationStore(Path(directory))).run(specification())
        sequence_calls = [request for request in provider.conversation_requests
                          if request.metadata.get("condition") == "sequential_attack"]
        self.assertEqual(len(sequence_calls[0].messages), 3)
        self.assertEqual(len(sequence_calls[1].messages), 5)
        self.assertEqual([item.role for item in sequence_calls[1].messages],
                         ["user", "assistant", "user", "assistant", "user"])

    def test_benchmark_seed_reaches_supported_provider(self):
        model = ModelMetadata("model", "mock")
        provider = MockInferenceProvider()
        with tempfile.TemporaryDirectory() as directory:
            run = BenchmarkEngine(InMemoryModelRegistry((model,)), provider,
                JsonBenchmarkStore(Path(directory))).run(
                    Dataset((DatasetRecord(id="case", prompt="prompt"),)),
                    BenchmarkConfig("model", run_id="seed-run", seed=77))
        metadata = run.results[0].response.generation_metadata
        self.assertEqual(metadata["effective_seed"], 77)
        self.assertTrue(metadata["provider_supports_seed"])

    def test_unknown_context_is_preserved_and_not_promoted_to_retained(self):
        class UnknownContextProvider(MockInferenceProvider):
            def generate_conversation(self, request):
                return replace(super().generate_conversation(request), context_status=ContextValidity.UNKNOWN,
                               metadata={"context_reason": "provider_omits_window_evidence"})
        provider = UnknownContextProvider(default_response="answer")
        with tempfile.TemporaryDirectory() as directory:
            values = ExperimentRunner(provider, ObservationStore(Path(directory))).run(specification())
        self.assertTrue(all(value.context_status is ContextValidity.UNKNOWN for value in values))
        self.assertFalse(any(value.context_status is ContextValidity.RETAINED for value in values))

    def test_provider_failure_becomes_immutable_failed_observation(self):
        class FailingProvider(MockInferenceProvider):
            def generate_conversation(self, request):
                if request.messages[-1].content == "attack two":
                    raise RuntimeError("fixture failure")
                return super().generate_conversation(request)
        provider = FailingProvider(default_response="answer")
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(Path(directory))
            values = ExperimentRunner(provider, store).run(specification())
            failed = [value for value in values if value.status.value == "failed"]
            self.assertEqual(len(failed), 2)
            self.assertTrue(all("fixture failure" in value.reason for value in failed))
            calls = len(provider.conversation_requests)
            ExperimentRunner(provider, store).run(specification())
            self.assertEqual(len(provider.conversation_requests), calls)

    def test_controlled_observations_build_matched_saea_and_recovery_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(Path(directory))
            ExperimentRunner(MockInferenceProvider(default_response="answer"), store).run(specification())
            observations = store.all()
        measurements = tuple(BehaviorMeasurement(item.observation_id, {"safety": .8, "helpfulness": .7},
            "behavior-v1", "fixture-judge") for item in observations)
        saea_input = build_saea_input(observations, measurements, sequence_id="case-sequence-1")
        saea = SAEAEngine().evaluate(saea_input)
        self.assertEqual(saea.status, ResultStatus.APPLICABLE)
        self.assertEqual(len(saea.per_step), 2)
        recovery_input = build_recovery_input(observations, measurements, sequence_id="case-sequence-1")
        calibration = RCCalibrationArtifact("fixture", "rc-reconciled-v1", "normalized_euclidean_v1",
            ("safety", "helpfulness"), .01)
        recovery = RecoveryCapabilityEngine().evaluate_run(recovery_input, calibration)
        self.assertEqual(recovery.status.value, "not_applicable")
        self.assertEqual(recovery.reason, "no_measurable_initial_degradation")


class ControlMatchingTests(unittest.TestCase):
    def test_exact_match_accepted_and_each_dimension_rejected(self):
        base = identity()
        self.assertTrue(validate_control_match(base, base).matched)
        changes = {
            "evaluation_case_id": "control_case_mismatch", "attack_id": "control_attack_mismatch",
            "attack_instance_id": "control_attack_instance_mismatch", "target_model": "control_model_mismatch",
            "target_model_version": "control_model_version_mismatch", "provider": "control_provider_mismatch",
            "generation_digest": "control_generation_mismatch", "dataset_version": "control_dataset_mismatch",
            "behavior_representation_version": "control_behavior_representation_mismatch",
            "layer1_version": "control_layer1_mismatch", "layer2_judge_version": "control_judge_mismatch",
            "measurement_version": "control_measurement_mismatch", "threat_model": "control_threat_model_mismatch",
        }
        for field_name, reason in changes.items():
            with self.subTest(field=field_name):
                result = validate_control_match(base, replace(base, **{field_name: "different"}))
                self.assertFalse(result.matched)
                self.assertEqual(result.reason, reason)

    def test_saea_refuses_mismatched_control(self):
        baseline = BehavioralState("b", {"safety": .9, "helpfulness": .9})
        attack = AttackInstance("attack-1", "attack", "cat", "family", 1, "case",
            BehavioralState("seq", {"safety": .2, "helpfulness": .2}),
            BehavioralState("iso", {"safety": .3, "helpfulness": .3}), (baseline,),
            sequential_identity=identity(), isolated_identity=identity(target_model="other"))
        result = SAEAEngine().evaluate(SAEAInput("run", "sequence", "model", "dataset", "dataset-v1",
            (baseline,), (attack,), SpacingCondition.STACKED, ContextStatus.RETAINED))
        self.assertEqual(result.per_step[0].status, ResultStatus.UNDEFINED)
        self.assertEqual(result.per_step[0].reason, "control_model_mismatch")
        self.assertIsNone(result.per_step[0].context_effect)


class OutcomeCalibrationAndAnalysisTests(unittest.TestCase):
    def test_human_import_and_classified_only_asr(self):
        rows = [
            {"evaluation_id": "1", "attack_family": "a", "status": "classified", "success": True},
            {"evaluation_id": "2", "attack_family": "a", "status": "failed", "success": True},
            {"evaluation_id": "3", "attack_family": "a", "status": "unavailable"},
            {"evaluation_id": "4", "attack_family": "a", "status": "ambiguous"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            records = import_human_outcomes(path, evaluator_id="human-rater", evaluator_version="v1",
                label_version="labels-v1", threat_model="injection")
        result = calculate_asr(records)
        self.assertEqual(result["denominator"], 1)
        self.assertEqual(result["attack_success_rate"], 1.0)
        self.assertEqual(records[0].label_source, "independent_human")
        self.assertIsNone(records[1].success)

    def test_calibration_metrics_coverage_and_provenance(self):
        pairs = (
            JudgeCalibrationPair("1", False, False, "a"),
            JudgeCalibrationPair("2", False, True, "a"),
            JudgeCalibrationPair("3", True, False, "b"),
            JudgeCalibrationPair("4", True, True, "b"),
            JudgeCalibrationPair("5", True, None, "b"),
        )
        artifact = build_judge_calibration_artifact(pairs, artifact_id="artifact",
            dataset="dataset", dataset_revision="rev", dataset_hash="hash",
            judge_provider="local", judge_model="judge", judge_model_version="digest",
            judge_prompt_version="prompt", rubric_version="rubric",
            label_mapping={"safe": 0, "unsafe": 1}, human_label_source="human",
            software_version="commit", bootstrap_resamples=100, bootstrap_seed=1)
        self.assertEqual(artifact.sample_size, 5)
        self.assertEqual(artifact.usable_sample_size, 4)
        self.assertEqual(artifact.coverage, .8)
        self.assertEqual(artifact.confusion_matrix, {"tn": 1, "fp": 1, "fn": 1, "tp": 1})
        self.assertEqual(artifact.precision, .5)
        self.assertEqual(artifact.recall, .5)
        self.assertEqual(artifact.f1, .5)
        self.assertEqual(artifact.validation_status, "not_validated")

    def test_paired_and_complementarity_are_conservative(self):
        analysis = paired_difference_analysis((PairedValue("1", .2, .4), PairedValue("2", .3, .7)),
            sample_definition="isolated vs sequential", resamples=100, seed=3)
        self.assertEqual(analysis.n, 2)
        self.assertAlmostEqual(analysis.statistic["mean_difference"], .3)
        raw = complementarity_table((ComplementarityRow("p", .5, .5, .1, .7),))
        self.assertEqual(raw["status"], "raw_only")
        self.assertEqual(raw["flagged_pair_ids"], ())
        exploratory = complementarity_table((ComplementarityRow("p", .5, .5, .1, .7),),
            similar_outcome_threshold=.01, material_trajectory_threshold=.5)
        self.assertEqual(exploratory["flagged_pair_ids"], ("p",))
        self.assertFalse(exploratory["scientifically_validated"])

    def test_dqi_missing_embeddings_is_unavailable_not_zero(self):
        result = calculate_dqi(Dataset((DatasetRecord(id="1", prompt="p"),)))
        self.assertIsNone(result.components["novelty"])
        self.assertIsNone(result.score)
        self.assertEqual(result.status, "unavailable")

    def test_manifest_hash_stable_and_persistence_append_only(self):
        self.assertEqual(stable_hash({"b": 2, "a": 1}), stable_hash({"a": 1, "b": 2}))
        engine = make_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            append_scientific_artifact(session, record_id="outcome", family="attack_outcome",
                schema_version="v1", scope="evaluation", owner_id="e1", status="classified",
                artifact={"success": True}, provenance={"source": "human"})
            with self.assertRaises(ValueError):
                append_scientific_artifact(session, record_id="outcome", family="attack_outcome",
                    schema_version="v1", scope="evaluation", owner_id="e1", status="classified",
                    artifact={"success": False})

    def test_manifest_records_unknown_values_with_reasons(self):
        spec = specification()
        with tempfile.TemporaryDirectory() as directory:
            observations = ExperimentRunner(MockInferenceProvider(default_response="a"),
                ObservationStore(Path(directory))).run(spec)
        manifest = build_manifest(spec, observations, root=str(Path(__file__).parents[1]),
            experiment_start="2026-01-01T00:00:00+00:00", experiment_end="2026-01-01T00:01:00+00:00")
        self.assertEqual(manifest.experiment_id, "experiment")
        self.assertEqual(manifest.requested_seeds, (17,))
        self.assertTrue(manifest.provider_supports_seed)
        self.assertIn("judge_identity", manifest.unavailable_reasons)


if __name__ == "__main__":
    unittest.main()
