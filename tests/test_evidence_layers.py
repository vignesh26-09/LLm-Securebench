import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from core.experiments.canary import CanaryPolicy, CanaryStatus, marker_for, verify_canary
from core.experiments.contamination import IsolationStatus, assess_isolation
from core.experiments.preregistration import amend_preregistration, compare_analysis_plan, lock_preregistration
from core.experiments.replication import compare_replay, export_bundle, load_bundle, write_bundle
from core.experiments.runner import ExperimentRunner, ObservationStore
from core.experiments.trajectory import BehaviorMeasurement, build_recovery_input, build_saea_input
from core.inference.mock import MockInferenceProvider
from core.saea.engine import SAEAEngine
from core.saea.models import ResultStatus
from tests.test_research_protocol import specification
from core.experiments.persistence import append_scientific_artifact
from core.persistence.database import Base, make_engine
from core.persistence.repositories import ScientificRecordRepository
from sqlalchemy.orm import Session


class EvidenceLayerTests(unittest.TestCase):
    def test_canary_marker_is_deterministic_and_provider_evidence_is_explicit(self):
        marker_id, marker = marker_for("experiment", "observation", 1)
        self.assertEqual((marker_id, marker), marker_for("experiment", "observation", 1))
        result = verify_canary(marker_id=marker_id, marker=marker, turn_index=1, prior_marker_ids=(),
                                metadata={"canary_verification": "verified"}, policy=CanaryPolicy(enabled=True))
        self.assertIs(result.status, CanaryStatus.VERIFIED)

    def test_failed_canary_blocks_saea_and_recovery(self):
        spec = replace(specification(), canary_policy={"enabled": True})
        with tempfile.TemporaryDirectory() as directory:
            values = ExperimentRunner(MockInferenceProvider(default_response="a"), ObservationStore(Path(directory))).run(spec)
        changed = tuple(replace(item, canary_evidence={"status": "canary_failed"}) for item in values)
        measurements = tuple(BehaviorMeasurement(item.observation_id, {"safety": .8, "helpfulness": .7}, "v", "fixture") for item in changed)
        saea = SAEAEngine().evaluate(build_saea_input(changed, measurements, sequence_id="case-sequence-1"))
        self.assertEqual(saea.reason, "context_window_validity_not_established")
        recovery = build_recovery_input(changed, measurements, sequence_id="case-sequence-1")
        self.assertEqual(recovery.context_status.value, "truncated")

    def test_preregistration_is_versioned_and_unplanned_analysis_is_labeled(self):
        locked = lock_preregistration(preregistration_id="p1", experiment_id="e", research_questions=("q",),
                                      planned_tests=("paired",), planned_metrics=("saea",), complementarity_procedure="table")
        amended = amend_preregistration(locked, preregistration_id="p2", amendment_reason="protocol correction")
        self.assertEqual(amended.version, 2)
        self.assertEqual(compare_analysis_plan(locked, analysis_id="a", requested_items=("paired",)).status, "as_planned")
        self.assertEqual(compare_analysis_plan(locked, analysis_id="b", requested_items=("new-test",)).status,
                         "exploratory_not_preregistered")

    def test_locked_preregistration_rejects_overwrite_and_keeps_versions_queryable(self):
        locked = lock_preregistration(preregistration_id="locked-v1", experiment_id="experiment",
            research_questions=("original research question",), planned_tests=("paired",),
            planned_metrics=("saea",), complementarity_procedure="table")
        original_hash = locked.content_hash
        attempted_overwrite = replace(locked, research_questions=("changed research question",),
                                      content_hash="changed-content-hash")
        amended = amend_preregistration(locked, preregistration_id="locked-v2",
            amendment_reason="pre-execution protocol correction", research_questions=("amended question",))
        engine = make_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            append_scientific_artifact(session, record_id=locked.preregistration_id,
                family="preregistration", schema_version="preregistration-v1", scope="experiment",
                owner_id=locked.experiment_id, status=locked.status.value, artifact=locked)
            with self.assertRaises(ValueError):
                append_scientific_artifact(session, record_id=attempted_overwrite.preregistration_id,
                    family="preregistration", schema_version="preregistration-v1", scope="experiment",
                    owner_id=locked.experiment_id, status=locked.status.value, artifact=attempted_overwrite)
            append_scientific_artifact(session, record_id=amended.preregistration_id,
                family="preregistration", schema_version="preregistration-v1", scope="experiment",
                owner_id=amended.experiment_id, status=amended.status.value, artifact=amended)
            repository = ScientificRecordRepository(session)
            persisted_original = repository.get(locked.preregistration_id)
            persisted_amendment = repository.get(amended.preregistration_id)
            self.assertEqual(persisted_original.payload["research_questions"], ["original research question"])
            self.assertEqual(persisted_original.payload["content_hash"], original_hash)
            self.assertEqual(persisted_amendment.payload["parent_preregistration_id"], locked.preregistration_id)
            self.assertEqual(persisted_amendment.payload["research_questions"], ["amended question"])

    def test_contamination_leak_blocks_isolated_delta(self):
        record = assess_isolation(record_id="c", sequential_observation_id="seq", isolated_observation_id="iso",
                                  sequential_conversation_id="same", isolated_conversation_id="same", provider="mock",
                                  sequential_metadata={}, isolated_metadata={})
        self.assertIs(record.status, IsolationStatus.SUSPECTED_LEAK)
        values = ExperimentRunner(MockInferenceProvider(default_response="a"), ObservationStore(Path(tempfile.mkdtemp()))).run(specification())
        measures = tuple(BehaviorMeasurement(item.observation_id, {"safety": .8, "helpfulness": .7}, "v", "fixture") for item in values)
        input_value = build_saea_input(values, measures, sequence_id="case-sequence-1", contamination_records=(
            replace(record, sequential_observation_id=next(x.observation_id for x in values if x.sequence_id == "case-sequence-1" and x.attack_instance_id == "attack-1"),
                    isolated_observation_id=next(x.observation_id for x in values if x.condition.value == "isolated_attack" and x.attack_instance_id == "attack-1")),))
        result = SAEAEngine().evaluate(input_value)
        self.assertEqual(result.per_step[0].reason, "control_contamination_suspected")

    def test_bundle_round_trip_and_factual_response_diff(self):
        with tempfile.TemporaryDirectory() as directory:
            values = ExperimentRunner(MockInferenceProvider(default_response="a"), ObservationStore(Path(directory) / "obs")).run(specification())
            bundle = export_bundle(bundle_id="bundle", specification=specification(), observations=values)
            path = Path(directory) / "bundle.json"
            write_bundle(bundle, path)
            loaded = load_bundle(path)
        report = compare_replay(loaded, values, replay_id="same")
        self.assertEqual(report.status, "identical")
        changed = (replace(values[0], response="changed"),) + values[1:]
        self.assertEqual(compare_replay(loaded, changed, replay_id="changed").differences[0].response_status, "different")


if __name__ == "__main__":
    unittest.main()
