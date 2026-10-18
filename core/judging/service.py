"""Provider-neutral orchestration for one-dimension Layer 2 judge measurements."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Mapping

from core.judging.applicability import DimensionApplicability
from core.judging.models import JudgeCase, JudgeConfig, JudgeDimension, JudgeLabel, JudgeResult, JudgmentStatus, utc_timestamp
from core.judging.prompting import JudgePromptBuilder, JudgeRubric
from core.judging.provider import JudgeProvider, JudgeProviderError, JudgeProviderRequest, JudgeTimeoutError

logger = logging.getLogger(__name__)


class JudgeOutputValidationError(ValueError):
    """Raised for malformed or schema-invalid judge JSON output."""


# Narrow aliases used only when a local model emits a human-readable name despite
# the explicit schema. They never map a requested dimension to a different one.
_DIMENSION_ALIASES = {
    "safety": JudgeDimension.SAFETY_STANCE.value,
    "safety_score": JudgeDimension.SAFETY_STANCE.value,
    "safety stance": JudgeDimension.SAFETY_STANCE.value,
    "helpfulness": JudgeDimension.INSTRUCTION_FOLLOWING.value,
    "instruction following": JudgeDimension.INSTRUCTION_FOLLOWING.value,
    "instruction_following_score": JudgeDimension.INSTRUCTION_FOLLOWING.value,
}


@dataclass(frozen=True, slots=True)
class _ParsedJudgeOutput:
    score: float | None
    label: JudgeLabel
    confidence: float | None
    rationale: str | None
    evidence_citations: tuple[str, ...]
    metadata: Mapping[str, object]
    uncertainty_reason: str | None
    recovered: bool


class JudgeService:
    """Evaluates applicable dimensions through the JudgeProvider port only."""
    def __init__(self, provider: JudgeProvider, config: JudgeConfig, rubrics: Mapping[JudgeDimension, JudgeRubric], *, prompt_builder: JudgePromptBuilder | None = None, applicability: DimensionApplicability | None = None) -> None:
        if provider.provider_name != config.provider_name:
            raise ValueError("judge provider and configuration provider_name must match")
        self._provider = provider
        self._config = config
        self._rubrics = dict(rubrics)
        self._prompt_builder = prompt_builder or JudgePromptBuilder()
        self._applicability = applicability or DimensionApplicability()

    def judge(self, case: JudgeCase, dimension: JudgeDimension, *, run_metadata: Mapping[str, object] | None = None) -> JudgeResult:
        run_metadata = dict(run_metadata or {})
        decision = self._applicability.assess(case, dimension)
        if not decision.applicable:
            return self._result(case, dimension, JudgmentStatus.SKIPPED, False, decision.reason, run_metadata=run_metadata)
        try:
            rubric = self._rubrics[dimension]
        except KeyError as error:
            raise ValueError(f"No rubric configured for dimension: {dimension.value}") from error
        logger.info("Layer 2 judge configuration provider=%s model=%s model_version=%s methodology=%s prompt=%s rubric=%s temperature=%s seed=%s timeout=%s", self._config.provider_name, self._config.model, self._config.model_version, self._config.methodology_version, self._config.prompt_version, rubric.version, self._config.temperature, self._config.seed, self._config.timeout_seconds)
        request = JudgeProviderRequest(self._prompt_builder.build(case, rubric), self._config)
        for attempt in range(1, self._config.max_retries + 2):
            try:
                response = self._provider.judge(request)
                parsed = _parse_output(response.raw_output, dimension)
                status = JudgmentStatus.REFUSED if parsed.label is JudgeLabel.REFUSE else JudgmentStatus.COMPLETED
                return self._result(
                    case, dimension, status, True, None, score=parsed.score, label=parsed.label,
                    confidence=parsed.confidence, uncertainty_reason=parsed.uncertainty_reason,
                    rationale=parsed.rationale, evidence_citations=parsed.evidence_citations,
                    generation_metadata={**dict(response.generation_metadata), "judge_output_metadata": dict(parsed.metadata), "json_recovered": parsed.recovered},
                    run_metadata=run_metadata, attempts=attempt,
                )
            except (JudgeOutputValidationError, JudgeTimeoutError, JudgeProviderError) as error:
                logger.warning("Layer 2 judge attempt %d failed for evaluation=%s dimension=%s: %s", attempt, case.evaluation_id, dimension.value, error)
                error_type = type(error).__name__
                error_message = str(error)
            except Exception as error:
                logger.exception("Unexpected Layer 2 judge failure for evaluation=%s dimension=%s", case.evaluation_id, dimension.value)
                error_type = type(error).__name__
                error_message = str(error)
            if attempt == self._config.max_retries + 1:
                return self._result(case, dimension, JudgmentStatus.FAILED, True, None, run_metadata=run_metadata, attempts=attempt, failure={"type": error_type, "message": error_message})
        raise AssertionError("unreachable")

    def _result(self, case: JudgeCase, dimension: JudgeDimension, status: JudgmentStatus, applicable: bool, applicability_reason: str | None, *, score: float | None = None, label: JudgeLabel | None = None, confidence: float | None = None, uncertainty_reason: str | None = None, rationale: str | None = None, evidence_citations: tuple[str, ...] = (), generation_metadata: Mapping[str, object] | None = None, run_metadata: Mapping[str, object] | None = None, attempts: int = 0, failure: Mapping[str, object] | None = None) -> JudgeResult:
        return JudgeResult(
            case.evaluation_id, case.case_id, dimension, status, applicable, applicability_reason,
            self._config.provider_name, self._config.model, self._config.model_version,
            self._config.methodology_version, self._config.prompt_version, self._config.rubric_version,
            score, label, confidence, uncertainty_reason, rationale, evidence_citations,
            dict(generation_metadata or {}), dict(run_metadata or {}), utc_timestamp(), attempts, failure,
        )


def _parse_output(raw_output: str, dimension: JudgeDimension) -> _ParsedJudgeOutput:
    value, recovered = _recover_json(raw_output)
    if not isinstance(value, dict):
        raise JudgeOutputValidationError("judge output must be a JSON object")
    reported_dimension = value.get("dimension")
    normalized_dimension = _normalize_dimension(reported_dimension)
    if normalized_dimension != dimension.value:
        raise JudgeOutputValidationError("judge output dimension does not match request")
    try:
        label = JudgeLabel(value["label"])
    except (KeyError, ValueError) as error:
        raise JudgeOutputValidationError("judge output has invalid label") from error
    score = value.get("score")
    if label is JudgeLabel.REFUSE:
        if score is not None:
            raise JudgeOutputValidationError("refused judge output must have null score")
        return _ParsedJudgeOutput(None, label, None, value.get("reason"), (), dict(value.get("metadata", {})), value.get("reason"), recovered)
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= float(score) <= 1.0:
        raise JudgeOutputValidationError("judge output score must be a number between 0 and 1")
    confidence = value.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0.0 <= float(confidence) <= 1.0):
        raise JudgeOutputValidationError("judge output confidence must be null or a number between 0 and 1")
    rationale = value.get("explanation")
    if not isinstance(rationale, str) or len(rationale) > 500:
        raise JudgeOutputValidationError("judge output explanation must be a concise string")
    evidence = value.get("evidence_citations")
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        raise JudgeOutputValidationError("judge output evidence_citations must be a string list")
    metadata = value.get("metadata", {})
    if not isinstance(metadata, dict):
        raise JudgeOutputValidationError("judge output metadata must be an object")
    metadata = dict(metadata)
    if reported_dimension != dimension.value:
        metadata["reported_dimension"] = reported_dimension
        metadata["dimension_normalized"] = normalized_dimension
    uncertainty_reason = metadata.get("reason_for_ambiguity")
    return _ParsedJudgeOutput(float(score), label, float(confidence) if confidence is not None else None, rationale, tuple(evidence), metadata, uncertainty_reason if isinstance(uncertainty_reason, str) else None, recovered)


def _normalize_dimension(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {item.value for item in JudgeDimension}:
        return normalized
    return _DIMENSION_ALIASES.get(normalized)


def _recover_json(raw_output: str) -> tuple[object, bool]:
    try:
        return json.loads(raw_output), False
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_output, flags=re.DOTALL)
        if match is None:
            raise JudgeOutputValidationError("judge output is not valid JSON") from None
        try:
            return json.loads(match.group(0)), True
        except json.JSONDecodeError as error:
            raise JudgeOutputValidationError("judge output does not contain recoverable JSON") from error
