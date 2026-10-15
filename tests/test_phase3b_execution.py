"""Synthetic-only enforcement tests; no scientific observations or labels."""

import json
import io
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from core.experiments.execution_gate import (planned_calls, sha256_file,
    verify_dataset_source, verify_local_protocol)
from core.experiments.dataset_audit import audit_research_manifest
from core.experiments.manifest import build_manifest
from core.experiments.models import (AttackDefinition, EvaluationCaseDesign,
    ExperimentSpecification, ExperimentalCondition, MeasurementConfiguration)
from core.experiments.runner import ExperimentRunner, ObservationStore
from core.inference import GenerationConfig
from core.inference.contracts import ConversationMessage, ConversationRequest, InferenceError
from core.inference.mock import MockInferenceProvider
from core.inference.ollama_provider import OllamaProvider
from core.models.registry import ModelMetadata
from core.persistence.database import make_engine
from core.persistence.models import ScientificRecordEntity
from scripts.run_controlled_experiment import _persist
from sqlalchemy.orm import Session


def fixture_spec():
    case = EvaluationCaseDesign(
        "fixture-case", "fixture baseline",
        tuple(AttackDefinition(f"a{index}", f"a{index}-1", "synthetic", f"attack {index}")
              for index in range(3)),
        (("a0-1", "a1-1", "a2-1"), ("a2-1", "a1-1", "a0-1")),
        ("recover 1", "recover 2"),
        ("benign 1", "benign 2", "benign 3"),
        ("recover 1", "recover 2"))
    return ExperimentSpecification(
        "fixture-experiment", "fixture-dataset", "fixture-v1", "placeholder",
        (ModelMetadata("fixture-model", "mock", "fixture-digest", 4096),),
        (case,), GenerationConfig(max_new_tokens=8), (1,), 1,
        MeasurementConfiguration("fixture-only", None, None, "fixture", None,
                                 "fixture-only", "synthetic"),
        preregistration_id="fixture-local-lock")


class Phase3BExecutionTests(unittest.TestCase):
    def test_complete_condition_budget_histories_and_resume(self):
        spec = fixture_spec()
        self.assertEqual(planned_calls(spec), 25)
        provider = MockInferenceProvider(default_response="fixture response")
        with tempfile.TemporaryDirectory() as directory:
            store = ObservationStore(Path(directory))
            observations = ExperimentRunner(provider, store).run(spec)
            self.assertEqual(len(observations), 25)
            benign = [value for value in observations
                      if value.condition is ExperimentalCondition.BENIGN_CONTROL]
            probes = [value for value in observations
                      if value.condition is ExperimentalCondition.BENIGN_RECOVERY]
            self.assertEqual(len(benign), 3)
            self.assertEqual(len(probes), 2)
            self.assertEqual(len(benign[-1].ordered_messages), 8)
            self.assertEqual(len(probes[-1].ordered_messages), 12)
            self.assertEqual({value.conversation_id for value in benign + probes},
                             {benign[0].conversation_id})
            self.assertFalse(any("attack" in str(value.ordered_messages)
                                 for value in benign + probes))
            calls = len(provider.conversation_requests)
            ExperimentRunner(provider, store).run(spec)
            self.assertEqual(len(provider.conversation_requests), calls)
            self.assertEqual(len(store.all()), 25)

    def test_source_and_local_lock_reject_mutation(self):
        spec = fixture_spec()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps({"dataset_id": spec.dataset_id,
                "dataset_version": spec.dataset_version,
                "cases": [asdict(spec.cases[0])]}), encoding="utf-8")
            spec = replace(spec, dataset_hash=sha256_file(source))
            self.assertEqual(verify_dataset_source(spec, source), spec.dataset_hash)
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps({"id": spec.experiment_id}), encoding="utf-8")
            lock = root / "lock.json"
            lock.write_text(json.dumps({"status": "locally_frozen",
                "experiment_id": spec.experiment_id, "dataset_sha256": spec.dataset_hash,
                "specification_sha256": sha256_file(spec_path),
                "preregistration_id": spec.preregistration_id}), encoding="utf-8")
            self.assertEqual(verify_local_protocol(spec, spec_path, lock)["status"],
                             "locally_frozen")
            source.write_text(source.read_text(encoding="utf-8") + " ", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dataset_source_hash_mismatch"):
                verify_dataset_source(spec, source)
            spec_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "protocol_specification_hash_mismatch"):
                verify_local_protocol(spec, spec_path, lock)

    def test_mismatched_controls_are_rejected(self):
        case = fixture_spec().cases[0]
        with self.assertRaisesRegex(ValueError, "match every attack sequence length"):
            replace(case, benign_control_prompts=("short",))
        with self.assertRaisesRegex(ValueError, "probe counts must match"):
            replace(case, benign_recovery_probes=("one",))

    def test_research_manifest_split_and_near_duplicate_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_text("fixture source", encoding="utf-8")
            def row(case_id, split, group, prompt):
                return {"case_id": case_id, "legitimate_task": "fixture task",
                    "attack_objective": "fixture objective", "attack_category": "fixture category",
                    "related_group_id": group, "split": split, "prompt": prompt}
            manifest = {"dataset_id": "fixture", "version": "v1", "source_revision": "fixture-rev",
                "license": "fixture", "source_sha256": sha256_file(source),
                "cases": [row("a", "development", "group-a", "alpha beta gamma"),
                          row("b", "test", "group-b", "delta epsilon zeta")]}
            self.assertEqual(audit_research_manifest(manifest, source)["status"],
                             "structurally_eligible")
            manifest["cases"][1]["related_group_id"] = "group-a"
            with self.assertRaisesRegex(ValueError, "related group crosses"):
                audit_research_manifest(manifest, source)
            manifest["cases"][1]["related_group_id"] = "group-b"
            manifest["cases"][1]["prompt"] = "Alpha beta gamma!"
            self.assertEqual(audit_research_manifest(manifest, source)["status"],
                             "review_required")
            manifest["source_sha256"] = "wrong"
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                audit_research_manifest(manifest, source)

    def test_fresh_pilot_database_is_initialized_and_classified(self):
        spec = fixture_spec()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observations = ExperimentRunner(MockInferenceProvider(default_response="fixture"),
                                            ObservationStore(root / "observations")).run(spec)
            manifest = build_manifest(spec, observations, root=str(Path(__file__).parents[1]),
                                      experiment_start="2026-01-01T00:00:00+00:00",
                                      experiment_end="2026-01-01T00:01:00+00:00")
            database = root / "fresh" / "pilot.db"
            _persist(database, spec, observations, manifest, "engineering_pilot")
            engine = make_engine(f"sqlite:///{database}")
            with Session(engine) as session:
                record = session.get(ScientificRecordEntity,
                    f"experiment:{spec.experiment_id}:observation:{observations[0].observation_id}")
                self.assertIsNotNone(record)
                self.assertEqual(record.provenance["reporting_class"], "engineering_pilot")
                self.assertIs(record.provenance["synthetic"], True)
            engine.dispose()

    def test_empty_ollama_text_is_failure_not_completed_observation(self):
        request = ConversationRequest(ModelMetadata("fixture", "ollama-local"), "conversation",
            (ConversationMessage("user", "fixture prompt", 0, "message"),))
        response = {"done": True, "done_reason": "length", "message": {"content": ""},
                    "prompt_eval_count": 5, "eval_count": 32}
        with patch("core.inference.ollama_provider.urlopen",
                   return_value=io.BytesIO(json.dumps(response).encode("utf-8"))):
            with self.assertRaisesRegex(InferenceError, "empty conversation response"):
                OllamaProvider().generate_conversation(request)


if __name__ == "__main__":
    unittest.main()
