"""Methodology-aligned dimension applicability decisions without score thresholds."""

from dataclasses import dataclass

from core.judging.models import JudgeCase, JudgeDimension


@dataclass(frozen=True, slots=True)
class ApplicabilityDecision:
    applicable: bool
    reason: str | None = None


class DimensionApplicability:
    """Applies documented prerequisites; skipped dimensions remain unscored."""
    def assess(self, case: JudgeCase, dimension: JudgeDimension) -> ApplicabilityDecision:
        if dimension in (JudgeDimension.CORRECTNESS, JudgeDimension.HALLUCINATION) and not case.reference_material:
            return ApplicabilityDecision(False, "grounding_material_missing")
        if dimension is JudgeDimension.INSTRUCTION_FOLLOWING and not case.success_criteria:
            return ApplicabilityDecision(False, "success_criteria_missing")
        if dimension is JudgeDimension.SAFETY_STANCE and not (case.attack_type_definition or case.threat_model):
            return ApplicabilityDecision(False, "threat_model_or_attack_definition_missing")
        if dimension is JudgeDimension.SEMANTIC_DRIFT and not all((case.benign_prompt, case.benign_response, case.attack_prompt, case.attack_response)):
            return ApplicabilityDecision(False, "before_after_pair_missing")
        if dimension is JudgeDimension.REASONING_QUALITY and not (case.correct_answer and case.task_type in {"math", "logic", "algorithm", "code"}):
            return ApplicabilityDecision(False, "grounded_reasoning_context_missing")
        if dimension is JudgeDimension.CONSISTENCY and not case.conversation_history:
            return ApplicabilityDecision(False, "conversation_history_missing")
        return ApplicabilityDecision(True)
