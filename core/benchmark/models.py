"""Provider-neutral benchmark execution schemas."""

from dataclasses import dataclass, field
from typing import Mapping

from core.inference.contracts import GenerationConfig, TokenUsage
from core.models.registry import ModelMetadata


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    """One dataset prompt scheduled for evaluation."""

    evaluation_id: str
    dataset_index: int
    record_id: str | None
    prompt: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Provider response data retained without coupling results to an SDK."""

    text: str
    provider: str
    latency_ms: float
    token_usage: TokenUsage | None = None
    finish_reason: str | None = None
    generation_metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Terminal outcome for one evaluation case; no security scoring is applied."""

    evaluation_id: str
    case: EvaluationCase
    status: str
    attempts: int
    response: ModelResponse | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    """A complete machine-readable benchmark execution record."""

    run_id: str
    model: ModelMetadata
    seed: int | None
    generation: GenerationConfig
    concurrency: int
    max_retries: int
    status: str
    results: tuple[EvaluationResult, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    """Execution settings that do not expose any concrete inference SDK."""

    model_name: str
    run_id: str | None = None
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    concurrency: int = 1
    max_retries: int = 0
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.concurrency <= 0:
            raise ValueError("concurrency must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
