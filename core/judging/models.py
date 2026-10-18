"""Provider-neutral Layer 2 semantic-judgment schemas.

Judge results are measurements with uncertainty, never ground truth or attack-success labels.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Mapping


class JudgeDimension(StrEnum):
    SAFETY_STANCE = "safety_stance"
    CORRECTNESS = "correctness"
    CONSISTENCY = "consistency"
    INSTRUCTION_FOLLOWING = "instruction_following"
    HALLUCINATION = "hallucination"
    REASONING_QUALITY = "reasoning_quality"
    SEMANTIC_DRIFT = "semantic_drift"


class JudgmentStatus(StrEnum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REFUSED = "refused"
    FAILED = "failed"


class JudgeLabel(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    AMBIGUOUS = "ambiguous"
    REFUSE = "refuse"


@dataclass(frozen=True, slots=True)
class JudgeCase:
    """Context available for an individual dimension judgment."""
    evaluation_id: str
    case_id: str
    prompt: str
    response: str
    reference_material: str | None = None
    success_criteria: str | None = None
    attack_type_definition: str | None = None
    threat_model: str | None = None
    task_type: str | None = None
    correct_answer: str | None = None
    conversation_history: tuple[str, ...] = ()
    benign_prompt: str | None = None
    benign_response: str | None = None
    attack_prompt: str | None = None
    attack_response: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JudgeConfig:
    provider_name: str
    model: str
    model_version: str | None
    methodology_version: str
    prompt_version: str
    rubric_version: str
    temperature: float = 0.0
    seed: int | None = None
    timeout_seconds: float | None = None
    max_retries: int = 0

    def __post_init__(self) -> None:
        if self.temperature < 0:
            raise ValueError("temperature must be non-negative")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


@dataclass(frozen=True, slots=True)
class JudgeResult:
    """A structured, dimension-specific measurement with applicability and uncertainty."""
    evaluation_id: str
    case_id: str
    dimension: JudgeDimension
    status: JudgmentStatus
    applicable: bool
    applicability_reason: str | None
    judge_provider: str
    judge_model: str
    judge_model_version: str | None
    methodology_version: str
    prompt_version: str
    rubric_version: str
    score: float | None = None
    label: JudgeLabel | None = None
    confidence: float | None = None
    uncertainty_reason: str | None = None
    rationale: str | None = None
    evidence_citations: tuple[str, ...] = ()
    generation_metadata: Mapping[str, object] = field(default_factory=dict)
    run_metadata: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = ""
    attempts: int = 0
    failure: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        for name, value in (("score", self.score), ("confidence", self.confidence)):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.status in (JudgmentStatus.SKIPPED, JudgmentStatus.FAILED, JudgmentStatus.REFUSED) and self.score is not None:
            raise ValueError("skipped, failed, and refused judgments must not contain a score")
        if self.status is JudgmentStatus.COMPLETED and (self.score is None or self.label is None):
            raise ValueError("completed judgments require score and label")
        if self.rationale is not None and len(self.rationale) > 500:
            raise ValueError("rationale must be concise (500 characters or fewer)")


def utc_timestamp() -> str:
    return datetime.now().astimezone().isoformat()
