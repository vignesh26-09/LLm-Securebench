"""Pinned 10,000-prompt corpus and bounded mock-run integration."""

import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.main import create_app
from core.dataset.benchmark_catalog import LARGE_KEY, dataset_options, load_selection
from core.inference.mock import MockInferenceProvider
from core.persistence.models import BenchmarkRunEntity, ScientificRecordEntity
from scripts import build_10000_corpus as builder
from scripts.run_local_benchmark import run_model


INVENTORY = [{"name": "test-model", "digest": "fixture-digest", "capabilities": []}]


class LargeCorpusTests(unittest.TestCase):
    def test_real_source_manifest_has_10000_distinct_prompt_inputs(self):
        selection = load_selection(LARGE_KEY, offset=9990, count=10)
        manifest = selection.manifest
        self.assertEqual(selection.source_count, 10000)
        self.assertEqual(selection.count, 10)
        self.assertEqual(manifest["category_counts"], {
            "benign_control_source": 5000, "red_team_source_seed": 5000})
        self.assertFalse(manifest["scientifically_validated"])
        self.assertFalse(manifest["outcome_labels_available"])
        self.assertEqual(len({row.prompt.casefold() for row in selection.dataset.records}), 10)
        self.assertEqual([row.category for row in selection.dataset.records[:2]],
                         ["red_team_source_seed", "benign_control_source"])
        self.assertTrue(next(item for item in dataset_options() if item["id"] == LARGE_KEY)["available"])
        for arguments in ({"offset": 9000, "count": 1001},
                          {"offset": 9900, "count": 101},
                          {"offset": -1, "count": 1}):
            with self.assertRaises(ValueError):
                load_selection(LARGE_KEY, **arguments)

    def test_builder_deduplicates_and_never_invents_outcome_labels(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as temporary:
            root = Path(temporary)
            dolly = root / "dolly.jsonl"
            anthropic = root / "anthropic.jsonl.gz"
            dolly_rows = [{"instruction": f"Explain harmless fixture topic {i} clearly.",
                           "context": "", "category": "general_qa", "response": "source answer"}
                          for i in range(4)]
            dolly.write_text("".join(json.dumps(row) + "\n" for row in dolly_rows), encoding="utf-8")
            red_rows = [{"transcript": f"\n\nHuman: Fixture red-team seed {i} for testing.\n\nAssistant: old source answer"}
                        for i in range(4)]
            with gzip.open(anthropic, "wt", encoding="utf-8") as output:
                json.dump(red_rows, output)
            pinned = {name: {**spec, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                      for (name, spec), path in zip(builder.SOURCES.items(), (dolly, anthropic))}
            corpus, manifest_path = root / "corpus.jsonl", root / "manifest.json"
            with patch.dict(builder.SOURCES, pinned, clear=True):
                manifest = builder.build_corpus(dolly, anthropic, corpus, manifest_path, per_group=2)
                self.assertEqual(builder.build_corpus(dolly, anthropic, corpus,
                                                     manifest_path, per_group=2), manifest)
                self.assertEqual(manifest["record_count"], 4)
                rows = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(len({row["prompt"] for row in rows}), 4)
                self.assertTrue(all(row["metadata"]["outcome_label_status"] == "not_collected"
                                    for row in rows))
                self.assertTrue(all("old source answer" not in row["prompt"] for row in rows))
                dolly.write_text(dolly.read_text(encoding="utf-8") + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    builder.build_corpus(dolly, anthropic, corpus, manifest_path, per_group=2)

    def test_two_case_mock_window_persists_large_source_provenance(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as temporary:
            root = Path(temporary)
            url = f"sqlite:///{root / 'test.db'}"
            app = create_app(url)
            result = run_model("test-model", database_url=url, provider=MockInferenceProvider(),
                               inventory=INVENTORY, output_directory=root / "runs",
                               dataset_key=LARGE_KEY, case_offset=9000, case_count=2)
            self.assertEqual(result["completed"], 2)
            client = TestClient(app)
            counts = client.get("/dashboard-summary").json()["counts"]
            self.assertEqual((counts["datasets"], counts["dataset-versions"],
                              counts["evaluations"]), (1, 1, 2))
            report = client.get(f"/benchmark-runs/{result['run_id']}/report").json()
            self.assertEqual(report["execution"]["total_cases"], 2)
            self.assertEqual(report["selection"]["status"], "evidence_review_required")
            version = client.get("/dataset-versions").json()["items"][0]
            self.assertEqual(version["payload"]["record_count"], 10000)
            self.assertEqual(version["payload"]["manifest"]["dataset_sha256"],
                             load_selection(LARGE_KEY, offset=0, count=1).source_sha256)
            self.assertNotIn("records", version["payload"])
            with Session(app.state.session_factory.kw["bind"]) as session:
                saved_run = session.get(BenchmarkRunEntity, result["run_id"])
                self.assertEqual(saved_run.dataset_version_id, version["id"])
                self.assertEqual(saved_run.payload["provenance"]["case_offset"], 9000)
                records = session.scalars(select(ScientificRecordEntity).where(
                    ScientificRecordEntity.owner_id == result["run_id"])).all()
                self.assertTrue(records)
                self.assertTrue(all(record.provenance["dataset_id"] ==
                                    "external:mixed-source-10000-v1" for record in records))
            app.state.session_factory.kw["bind"].dispose()

    def test_api_requires_full_dataset_selection_without_generation(self):
        client = TestClient(create_app("sqlite:///:memory:", enable_local_runs=True),
                            client=("127.0.0.1", 50000))
        catalog = client.get("/benchmark-datasets").json()
        large = next(item for item in catalog["items"] if item["id"] == LARGE_KEY)
        self.assertTrue(large["available"])
        self.assertEqual((large["case_count"], large["max_cases_per_job"]), (10000, 10000))
        with patch("apps.api.local_execution.installed_models", return_value=INVENTORY), \
             patch("apps.api.local_execution.threading.Thread") as thread:
            invalid = client.post("/internal/benchmark-jobs", json={
                "model": "test-model", "dataset_key": LARGE_KEY,
                "case_offset": 9999, "case_count": 2}, headers={"X-SecureLLM-Local": "1"})
            self.assertEqual(invalid.status_code, 422)
            valid = client.post("/internal/benchmark-jobs", json={
                "model": "test-model", "dataset_key": LARGE_KEY,
                "case_offset": 0, "case_count": 10000, "confirm_full_corpus": True}, headers={"X-SecureLLM-Local": "1"})
            self.assertEqual(valid.status_code, 202)
            self.assertEqual(valid.json()["source_count"], 10000)
            self.assertEqual(valid.json()["case_count"], 10000)
            thread.return_value.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
