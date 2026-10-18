"""Unit tests for source-agnostic dataset ingestion and processing."""

import json
import tempfile
import unittest
from pathlib import Path

from core.dataset.duplicates import find_dataset_duplicates, prompt_sha256
from core.dataset.ingestion import loader_for_path
from core.dataset.loaders import CsvDatasetLoader, JsonDatasetLoader, JsonlDatasetLoader
from core.dataset.models import Dataset, DatasetRecord
from core.dataset.normalization import TextNormalizer, normalize_text
from core.dataset.splitting import split_train_evaluation
from core.dataset.statistics import calculate_dataset_statistics
from core.dataset.validation import DatasetValidationError


class DatasetLoaderTest(unittest.TestCase):
    def _path(self, suffix: str, content: str) -> Path:
        temporary = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, encoding="utf-8", delete=False)
        self.addCleanup(Path(temporary.name).unlink)
        temporary.write(content)
        temporary.close()
        return Path(temporary.name)

    def test_json_loader_reads_records_and_version_metadata(self) -> None:
        path = self._path(".json", json.dumps({
            "metadata": {"name": "sample", "version": {"version": "1.0", "checksum": "abc"}},
            "records": [{"id": "a", "prompt": "hello", "category": "test"}],
        }))
        dataset = JsonDatasetLoader().load(path)
        self.assertEqual(dataset.records[0].prompt, "hello")
        self.assertEqual(dataset.metadata.name, "sample")
        self.assertEqual(dataset.metadata.version.version, "1.0")

    def test_jsonl_and_csv_loaders(self) -> None:
        jsonl = self._path(".jsonl", '{"id":"a","prompt":"one"}\n{"prompt":"two","language":"en"}\n')
        csv_file = self._path(".csv", 'id,prompt,metadata\na,one,"{""origin"": ""unit""}"\n')
        self.assertEqual(len(JsonlDatasetLoader().load(jsonl).records), 2)
        csv_dataset = CsvDatasetLoader().load(csv_file)
        self.assertEqual(csv_dataset.records[0].metadata, {"origin": "unit"})
        self.assertIsInstance(loader_for_path(csv_file), CsvDatasetLoader)

    def test_invalid_records_are_rejected(self) -> None:
        no_identity = self._path(".json", '[{"category": "test"}]')
        unknown_field = self._path(".json", '[{"id": "a", "unrecognized": true}]')
        with self.assertRaisesRegex(DatasetValidationError, "at least an id or prompt"):
            JsonDatasetLoader().load(no_identity)
        with self.assertRaisesRegex(DatasetValidationError, "unknown fields"):
            JsonDatasetLoader().load(unknown_field)

    def test_missing_optional_fields_are_supported(self) -> None:
        path = self._path(".json", '[{"id": "only-id"}]')
        record = JsonDatasetLoader().load(path).records[0]
        self.assertEqual(record.id, "only-id")
        self.assertIsNone(record.prompt)
        self.assertEqual(record.metadata, {})


class DatasetProcessingTest(unittest.TestCase):
    def test_normalization_is_conservative_and_unicode_aware(self) -> None:
        self.assertEqual(normalize_text("  cafe\u0301\r\nhello\tworld  "), "café\nhello world")
        dataset = Dataset((DatasetRecord(id=" x ", prompt="  hello\tworld "),))
        self.assertEqual(TextNormalizer().process(dataset).records[0].prompt, "hello world")

    def test_duplicate_detection_uses_normalized_sha256(self) -> None:
        dataset = Dataset((
            DatasetRecord(id="first", prompt="same\tprompt"),
            DatasetRecord(id="second", prompt=" same prompt "),
            DatasetRecord(id="third", prompt="different"),
        ))
        groups = find_dataset_duplicates(dataset)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].record_ids, ("first", "second"))
        self.assertEqual(groups[0].sha256, prompt_sha256("same prompt"))

    def test_dataset_statistics_and_split(self) -> None:
        dataset = Dataset((
            DatasetRecord(id="a", prompt="one", category="jailbreak", language="en"),
            DatasetRecord(id="b", prompt=None, attack_type="injection"),
            DatasetRecord(id="c", prompt="three", category="jailbreak", language="en"),
        ))
        stats = calculate_dataset_statistics(dataset)
        self.assertEqual(stats.record_count, 3)
        self.assertEqual(stats.prompt_count, 2)
        self.assertEqual(stats.missing_field_counts["prompt"], 1)
        self.assertEqual(stats.category_counts, {"jailbreak": 2})
        split = split_train_evaluation(dataset, evaluation_fraction=0.5, seed="test")
        self.assertEqual(len(split.train.records) + len(split.evaluation.records), 3)
