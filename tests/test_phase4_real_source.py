"""Phase 4 provenance and gate tests; never synthesize scientific outcomes."""

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from core.experiments.context_audit import audit_request_histories
from core.experiments.execution_gate import (
    planned_calls, verify_dataset_source, verify_local_protocol,
)
from core.experiments.runner import ObservationStore
from core.experiments.specification import load_experiment_specification
from scripts import build_phase4_dataset_manifest as manifest_script
from scripts import fetch_phase4_jbb_sources, inspect_phase4_jbb, prepare_phase4_jbb_pilot


ROOT = Path(__file__).resolve().parents[1]
PHASE4 = ROOT / "experiments" / "phase4"


class Phase4RealSourceTests(unittest.TestCase):
    def test_fetcher_verifies_local_sources_without_network(self):
        with patch.object(fetch_phase4_jbb_sources, "_get",
                          side_effect=AssertionError("network must not be used")):
            result = fetch_phase4_jbb_sources.fetch()
        self.assertEqual(len(result), 7)
        self.assertEqual(set(result.values()), {"already_verified"})

    def test_fetcher_never_writes_unverified_or_overwrites_modified_source(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "source.csv"
            content = b"safe fixture source"
            digest = hashlib.sha256(content).hexdigest()
            with patch.object(fetch_phase4_jbb_sources, "_get", return_value=b"wrong"):
                with self.assertRaisesRegex(ValueError, "upstream checksum mismatch"):
                    fetch_phase4_jbb_sources._download_verified("https://example.test", destination,
                                                                digest)
            self.assertFalse(destination.exists())
            with patch.object(fetch_phase4_jbb_sources, "_get", return_value=content):
                self.assertEqual(fetch_phase4_jbb_sources._download_verified(
                    "https://example.test", destination, digest), "downloaded_and_verified")
            destination.write_bytes(b"modified")
            with patch.object(fetch_phase4_jbb_sources, "_get",
                              side_effect=AssertionError("network must not be used")):
                with self.assertRaises(FileExistsError):
                    fetch_phase4_jbb_sources._download_verified("https://example.test",
                                                                destination, digest)

    def test_pinned_source_alignment_and_selected_cases(self):
        result = inspect_phase4_jbb.audit()
        self.assertEqual((result["harmful_rows"], result["benign_rows"]), (100, 100))
        self.assertEqual(len(result["artifact_complete_matching_indices"]), 79)
        self.assertEqual(result["historical_calibration_goal_overlap_count"], 9)
        self.assertEqual(result["historical_calibration_near_overlap_count"], 13)
        eligible = {row["index"] for row in result["artifact_complete_matching_indices"]}
        self.assertTrue(set(prepare_phase4_jbb_pilot.INDICES) <= eligible)
        self.assertFalse(set(prepare_phase4_jbb_pilot.INDICES) &
                         set(result["historical_calibration_near_overlap_indices"]))

    def test_local_lock_and_source_are_verified_before_calls(self):
        dataset = PHASE4 / "jbb_pilot_dataset_v1.json"
        spec_path = PHASE4 / "jbb_pilot_specification_v1.json"
        lock = PHASE4 / "jbb_pilot_local_lock_v1.json"
        spec = load_experiment_specification(spec_path)
        self.assertEqual(verify_dataset_source(spec, dataset), spec.dataset_hash)
        self.assertEqual(verify_local_protocol(spec, spec_path, lock)["status"],
                         "locally_frozen")
        self.assertEqual(planned_calls(spec), 100)
        self.assertEqual(spec.metadata["evidence_class"], "exploratory")
        self.assertIs(spec.metadata["scientific_eligibility"], False)
        self.assertIs(json.loads(lock.read_text(encoding="utf-8"))["external_registration"],
                      False)

    def test_separate_manifest_is_immutable_and_preserves_source_class(self):
        source = PHASE4 / "jbb_pilot_dataset_v1.json"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / source.name).write_bytes(source.read_bytes())
            with patch.object(manifest_script, "OUT", output):
                first = manifest_script.build()
                second = manifest_script.build()
                self.assertEqual(first, second)
                path = output / "jbb_research_manifest_v1.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["research_status"],
                                 "real_source_exploratory_pilot_not_confirmatory")
                self.assertEqual(data["selected_case_ids"], ["jbb-1", "jbb-51"])
                self.assertEqual(data["dataset_source_sha256"],
                                 hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(data["split"],
                                 "exploratory_pilot_only; no development/validation/held-out claim")
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                with self.assertRaises(FileExistsError):
                    manifest_script.build()

    def test_saved_request_history_audit_does_not_claim_provider_isolation(self):
        observations = ObservationStore(PHASE4 / "jbb_pilot_run_v1" / "observations").all()
        result = audit_request_histories(observations)
        self.assertEqual(result["status"], "request_history_consistent")
        self.assertEqual(result["observation_count"], 100)
        self.assertEqual(result["conversation_count"], 28)
        self.assertEqual(result["provider_session_isolation"],
                         "unverifiable_from_request_history")
        self.assertIs(result["context_retention_proof"], False)

        original = observations[0]
        broken = replace(original, ordered_messages=(
            *original.ordered_messages[:-1],
            {**original.ordered_messages[-1], "role": "user"},
        ))
        amended = [broken if item.observation_id == original.observation_id else item
                   for item in observations]
        damaged = audit_request_histories(amended)
        self.assertEqual(damaged["status"], "request_history_inconsistent")
        self.assertTrue(damaged["issues"])
        self.assertIs(damaged["context_retention_proof"], False)

    def test_annotation_export_contains_real_responses_but_no_labels(self):
        restricted = PHASE4 / "restricted_annotation"
        batch = json.loads((restricted / "blinded_batch_v1.json").read_text(encoding="utf-8"))
        mapping = json.loads((restricted / "private_join_map_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(batch["items"]), 36)
        self.assertEqual(len(mapping["mapping"]), 36)
        for item in batch["items"]:
            self.assertTrue(item["target_response"])
            self.assertEqual(set(item), {"adversarial_objective", "conversation_history",
                                         "legitimate_task", "sample_id", "target_response"})
            self.assertIn(item["sample_id"], mapping["mapping"])
            self.assertNotIn("outcome", item)
            self.assertNotIn("model", item)
            self.assertNotIn("source_artifact", item)
        summary = json.loads((PHASE4 / "jbb_pilot_run_v1" / "audit_summary.json").read_text(
            encoding="utf-8"))
        self.assertEqual(summary["human_labels"], 0)
        self.assertEqual(summary["scientific_metrics"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()
