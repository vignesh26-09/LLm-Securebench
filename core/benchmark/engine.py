"""Concurrent provider-neutral benchmark orchestration without security scoring."""

import hashlib
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from core.benchmark.models import BenchmarkConfig, BenchmarkRun, EvaluationCase, EvaluationResult, ModelResponse
from core.benchmark.storage import JsonBenchmarkStore
from core.dataset.ingestion import loader_for_path
from core.dataset.models import Dataset
from core.inference.contracts import InferenceError, InferenceProvider, InferenceRequest, InferenceTimeoutError
from core.models.registry import ModelMetadata, ModelRegistry

logger = logging.getLogger(__name__)


class BenchmarkEngine:
    """Coordinates datasets, a model registry, and an inference-provider port."""

    def __init__(self, registry: ModelRegistry, provider: InferenceProvider, store: JsonBenchmarkStore) -> None:
        self._registry = registry
        self._provider = provider
        self._store = store

    def run_from_path(self, dataset_path: Path, config: BenchmarkConfig, *, resume: bool = False) -> BenchmarkRun:
        """Load a processed supported dataset and execute it through the provider port."""
        return self.run(loader_for_path(dataset_path).load(dataset_path), config, resume=resume)

    def run(self, dataset: Dataset, config: BenchmarkConfig, *, resume: bool = False, progress_callback=None) -> BenchmarkRun:
        model = self._registry.get(config.model_name)
        run_id = config.run_id or uuid.uuid4().hex
        cases = self._cases(dataset, run_id, config.seed)
        existing = self._store.load(run_id) if resume else None
        if existing is not None and existing.model != model:
            raise ValueError(f"Cannot resume run '{run_id}' with a different model")
        completed = {result.evaluation_id: result for result in existing.results if result.status == "completed"} if existing else {}
        pending = [case for case in cases if case.evaluation_id not in completed]
        logger.info("Executing benchmark run %s with %d pending cases", run_id, len(pending))
        executed = self._execute_cases(pending, model, config, progress_callback=progress_callback, total_cases=len(cases))
        results = tuple(sorted((*completed.values(), *executed), key=lambda result: result.case.dataset_index))
        status = "completed" if all(result.status == "completed" for result in results) else "completed_with_errors"
        run = BenchmarkRun(run_id, model, config.seed, config.generation, config.concurrency, config.max_retries, status, results)
        self._store.save(run)
        return run

    def _cases(self, dataset: Dataset, run_id: str, seed: int | None) -> tuple[EvaluationCase, ...]:
        cases: list[EvaluationCase] = []
        for index, record in enumerate(dataset.records):
            if not record.prompt:
                continue
            identity = record.id or hashlib.sha256(record.prompt.encode("utf-8")).hexdigest()
            evaluation_id = hashlib.sha256(f"{run_id}:{seed}:{index}:{identity}".encode("utf-8")).hexdigest()[:24]
            cases.append(EvaluationCase(evaluation_id, index, record.id, record.prompt, dict(record.metadata)))
        return tuple(cases)

    def _execute_cases(self, cases: list[EvaluationCase], model: ModelMetadata, config: BenchmarkConfig, *, progress_callback=None, total_cases: int | None = None) -> tuple[EvaluationResult, ...]:
        with ThreadPoolExecutor(max_workers=config.concurrency, thread_name_prefix="benchmark") as executor:
            futures = [executor.submit(self._evaluate, case, model, config) for case in cases]
            results: list[EvaluationResult] = []
            for future in futures:
                result = future.result()
                results.append(result)
                if progress_callback is not None:
                    progress_callback("Generating responses", completed_cases=len(results), total_cases=total_cases or len(cases),
                                      last_case_id=result.case.record_id, last_latency_ms=result.response.latency_ms if result.response else None)
            return tuple(results)

    def _evaluate(self, case: EvaluationCase, model: ModelMetadata, config: BenchmarkConfig) -> EvaluationResult:
        for attempt in range(1, config.max_retries + 2):
            error_message: str | None = None
            try:
                result = self._provider.generate(InferenceRequest(model, case.prompt, config.generation, config.seed))
                response = ModelResponse(
                    text=result.text, provider=result.provider, latency_ms=result.latency_ms,
                    token_usage=result.token_usage, finish_reason=result.finish_reason,
                    generation_metadata=dict(result.metadata),
                )
                return EvaluationResult(case.evaluation_id, case, "completed", attempt, response)
            except InferenceTimeoutError as error:
                logger.warning("Evaluation %s timed out on attempt %d", case.evaluation_id, attempt)
                terminal_status = "timed_out"
                error_message = str(error)
            except Exception as error:
                logger.warning("Evaluation %s failed on attempt %d: %s", case.evaluation_id, attempt, error)
                terminal_status = "failed"
                error_message = str(error)
            if attempt == config.max_retries + 1:
                return EvaluationResult(case.evaluation_id, case, terminal_status, attempt, error=error_message)
        raise AssertionError("unreachable")
