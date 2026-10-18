"""JSON storage adapter for machine-readable benchmark results."""

import json
from dataclasses import asdict
from pathlib import Path

from core.benchmark.models import BenchmarkRun, EvaluationCase, EvaluationResult, ModelResponse
from core.inference.contracts import GenerationConfig, TokenUsage
from core.models.registry import ModelMetadata


class JsonBenchmarkStore:
    """Stores each run as one portable JSON document in a caller-owned directory."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def path_for(self, run_id: str) -> Path:
        return self._directory / f"{run_id}.json"

    def save(self, run: BenchmarkRun) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        target = self.path_for(run.run_id)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(_json_ready(asdict(run)), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(target)
        return target

    def load(self, run_id: str) -> BenchmarkRun | None:
        path = self.path_for(run_id)
        if not path.exists():
            return None
        return _parse_run(json.loads(path.read_text(encoding="utf-8")))


def _parse_run(value: dict[str, object]) -> BenchmarkRun:
    model_value = dict(value["model"])
    model_value["capabilities"] = frozenset(model_value.get("capabilities", ()))
    model = ModelMetadata(**model_value)
    generation = GenerationConfig(**dict(value["generation"]))
    results = tuple(_parse_result(dict(result)) for result in value["results"])
    return BenchmarkRun(
        run_id=str(value["run_id"]), model=model, seed=value.get("seed"), generation=generation,
        concurrency=int(value["concurrency"]), max_retries=int(value["max_retries"]),
        status=str(value["status"]), results=results,
    )


def _parse_result(value: dict[str, object]) -> EvaluationResult:
    case = EvaluationCase(**dict(value["case"]))
    response_value = value.get("response")
    response = None
    if response_value is not None:
        response_data = dict(response_value)
        usage = response_data.get("token_usage")
        response_data["token_usage"] = TokenUsage(**usage) if usage is not None else None
        response = ModelResponse(**response_data)
    return EvaluationResult(
        evaluation_id=str(value["evaluation_id"]), case=case, status=str(value["status"]),
        attempts=int(value["attempts"]), response=response, error=value.get("error"),
    )


def _json_ready(value: object) -> object:
    """Convert immutable collection values in domain schemas into JSON values."""
    if isinstance(value, frozenset):
        return sorted(_json_ready(item) for item in value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value
