"""End-to-end tests for the provider-neutral benchmark engine."""

import json
import tempfile
import unittest
from pathlib import Path

from core.benchmark.engine import BenchmarkEngine
from core.benchmark.models import BenchmarkConfig
from core.benchmark.storage import JsonBenchmarkStore
from core.dataset.models import Dataset, DatasetRecord
from core.inference.contracts import GenerationConfig, InferenceError
from core.inference.mock import MockInferenceProvider
from core.models.registry import InMemoryModelRegistry, ModelMetadata


class FailingProvider:
    provider_name = "failing"

    def generate(self, request: object) -> object:
        raise InferenceError("provider failure")


class FlakyProvider:
    provider_name = "flaky"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = MockInferenceProvider(default_response="recovered")

    def generate(self, request: object) -> object:
        self.calls += 1
        if self.calls == 1:
            raise InferenceError("transient failure")
        return self._delegate.generate(request)


class BenchmarkEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = JsonBenchmarkStore(Path(self.directory.name))
        self.model = ModelMetadata("mock-model", "mock")
        self.registry = InMemoryModelRegistry((self.model,))
        self.dataset = Dataset((
            DatasetRecord(id="one", prompt="first"),
            DatasetRecord(id="two", prompt="second"),
            DatasetRecord(id="skip", prompt=None),
        ))

    def _engine(self, provider: object) -> BenchmarkEngine:
        return BenchmarkEngine(self.registry, provider, self.store)

    def test_successful_run_is_stored_as_machine_readable_json(self) -> None:
        run = self._engine(MockInferenceProvider({"first": "a", "second": "b"})).run(
            self.dataset, BenchmarkConfig("mock-model", run_id="successful", concurrency=2, seed=7),
        )
        self.assertEqual(run.status, "completed")
        self.assertEqual([result.response.text for result in run.results if result.response], ["a", "b"])
        stored = json.loads(self.store.path_for("successful").read_text(encoding="utf-8"))
        self.assertEqual(stored["run_id"], "successful")
        self.assertEqual(len(stored["results"]), 2)

    def test_run_from_path_loads_supported_processed_dataset(self) -> None:
        path = Path(self.directory.name) / "processed.json"
        path.write_text('{"records": [{"id": "path", "prompt": "from path"}]}', encoding="utf-8")
        run = self._engine(MockInferenceProvider({"from path": "loaded"})).run_from_path(
            path, BenchmarkConfig("mock-model", run_id="path-run"),
        )
        self.assertEqual(run.results[0].response.text, "loaded")

    def test_failed_inference_is_captured(self) -> None:
        run = self._engine(FailingProvider()).run(self.dataset, BenchmarkConfig("mock-model", run_id="failed"))
        self.assertEqual(run.status, "completed_with_errors")
        self.assertTrue(all(result.status == "failed" for result in run.results))
        self.assertTrue(all(result.error == "provider failure" for result in run.results))

    def test_timeout_is_captured(self) -> None:
        provider = MockInferenceProvider(delay_seconds=0.1)
        config = BenchmarkConfig("mock-model", run_id="timeout", generation=GenerationConfig(timeout_seconds=0.01))
        run = self._engine(provider).run(self.dataset, config)
        self.assertTrue(all(result.status == "timed_out" for result in run.results))

    def test_retry_recovers_transient_failure(self) -> None:
        provider = FlakyProvider()
        run = self._engine(provider).run(self.dataset, BenchmarkConfig("mock-model", run_id="retry", max_retries=1, concurrency=1))
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.results[0].attempts, 2)
        self.assertEqual(provider.calls, 3)

    def test_resume_reexecutes_only_incomplete_cases(self) -> None:
        config = BenchmarkConfig("mock-model", run_id="resume", concurrency=1)
        first = self._engine(FailingProvider()).run(self.dataset, config)
        self.assertEqual(first.status, "completed_with_errors")
        resumed = self._engine(MockInferenceProvider(default_response="done")).run(self.dataset, config, resume=True)
        self.assertEqual(resumed.status, "completed")
        self.assertTrue(all(result.response and result.response.text == "done" for result in resumed.results))

    def test_execution_ids_are_deterministic_for_fixed_run_id_and_seed(self) -> None:
        config = BenchmarkConfig("mock-model", run_id="deterministic", seed=99, concurrency=2)
        first = self._engine(MockInferenceProvider(default_response="same")).run(self.dataset, config)
        other_directory = tempfile.TemporaryDirectory()
        self.addCleanup(other_directory.cleanup)
        second_engine = BenchmarkEngine(self.registry, MockInferenceProvider(default_response="same"), JsonBenchmarkStore(Path(other_directory.name)))
        second = second_engine.run(self.dataset, config)
        self.assertEqual([result.evaluation_id for result in first.results], [result.evaluation_id for result in second.results])
        self.assertEqual([result.response.text for result in first.results if result.response], [result.response.text for result in second.results if result.response])
