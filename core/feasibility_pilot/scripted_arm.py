"""S replay is a separately tagged mechanism, never a live primary arm."""

from dataclasses import dataclass, field
from enum import StrEnum

from core.feasibility_pilot.allocation import Arm, TrialAssignment
from core.feasibility_pilot.live_arms import UserStep, StepKind
from core.feasibility_pilot.restricted_store import RestrictedEvidenceStore


class ScriptLabel(StrEnum):
    REFUSAL = "refusal"
    COMPLIANCE = "compliance"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class ScriptedAssistantTurn:
    text: str = field(repr=False)
    label: ScriptLabel = ScriptLabel.NEUTRAL
    script_version: str = ""

    def __post_init__(self) -> None:
        if not self.text.strip() or not self.script_version:
            raise ValueError("Scripted assistant turn requires text and version")


@dataclass(frozen=True, slots=True)
class ScriptedPlan:
    assignment: TrialAssignment
    exposure_user: UserStep = field(repr=False)
    scripted_assistant: ScriptedAssistantTurn = field(repr=False)
    later_steps: tuple[UserStep, ...] = field(repr=False)
    evidence_class: str = "scripted_mechanism"
    eligible_live_primary: bool = False

    def __post_init__(self) -> None:
        if (self.assignment.arm != Arm.S or self.assignment.evidence_class != "scripted_mechanism"
                or self.eligible_live_primary or self.evidence_class != "scripted_mechanism"):
            raise ValueError("Scripted replay cannot enter live population")
        if self.exposure_user.kind == StepKind.FINAL_PROBE or not self.later_steps or self.later_steps[-1].kind != StepKind.FINAL_PROBE:
            raise ValueError("Invalid S exposure/final schedule")
        if self.scripted_assistant.script_version != self.assignment.script_version:
            raise ValueError("Script version differs from allocation")


def validate_scripted_plan(plan: ScriptedPlan, store: RestrictedEvidenceStore) -> None:
    store.assert_public_safe(plan.scripted_assistant.text)
    store.assert_public_safe(plan.exposure_user.text)
    for step in plan.later_steps:
        store.assert_public_safe(step.text)
