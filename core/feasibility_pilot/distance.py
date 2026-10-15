"""Versioned post-exposure exchange schedules; no model calls."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict

from core.feasibility_pilot.allocation import Arm
from core.feasibility_pilot.cases import digest
from core.feasibility_pilot.live_arms import LivePlan, StepKind, UserStep
from core.feasibility_pilot.scripted_arm import ScriptedPlan


SCHEDULE_VERSION = "exchange-distance-v1"


@dataclass(frozen=True, slots=True)
class DistanceSchedule:
    trial_id: str
    assigned_distance: int | None
    exposure_sha256: str
    filler_step_sha256: tuple[str, ...]
    final_probe_sha256: str
    planned_filler_exchanges: int
    planned_token_distance: int | None = None
    token_estimator_reference: str | None = None
    token_control_group_id: str | None = None
    schedule_version: str = SCHEDULE_VERSION

    def __post_init__(self) -> None:
        if self.schedule_version != SCHEDULE_VERSION:
            raise ValueError("Unsupported distance schedule version")
        if self.assigned_distance is not None and self.assigned_distance not in {0, 2, 5}:
            raise ValueError("Unapproved exchange distance")
        if self.planned_filler_exchanges != len(self.filler_step_sha256):
            raise ValueError("Filler schedule count mismatch")
        if self.planned_filler_exchanges != (self.assigned_distance or 0):
            raise ValueError("Filler schedule differs from frozen assignment")
        if self.planned_token_distance is not None and self.planned_token_distance < 0:
            raise ValueError("Planned token distance must be nonnegative")
        if self.planned_token_distance is not None and not self.token_estimator_reference:
            raise ValueError("Token estimate requires source reference")

    @property
    def content_sha256(self) -> str:
        return digest(asdict(self))


def _step_digest(step: UserStep) -> str:
    return digest((step.kind.value, step.text, step.script_id))


def build_distance_schedule(plan: LivePlan | ScriptedPlan, *,
                            planned_token_distance: int | None = None,
                            token_estimator_reference: str | None = None,
                            token_control_group_id: str | None = None) -> DistanceSchedule:
    """Validate exposure -> exactly d filler exchanges -> final probe.

    Each filler is a *planned user step*. Its completion is counted later only
    after a valid defender-provider response has been recorded.
    """
    assignment = plan.assignment
    if isinstance(plan, LivePlan):
        if assignment.arm == Arm.S:
            raise ValueError("S requires a scripted mechanism plan")
        if not plan.steps or plan.steps[-1].kind != StepKind.FINAL_PROBE:
            raise ValueError("Legitimate final probe must be last")
        before_final = plan.steps[:-1]
        if assignment.arm == Arm.B0:
            if assignment.distance is not None or before_final:
                raise ValueError("B0 has no exposure and distance is not applicable")
            exposure: tuple[UserStep, ...] = ()
            fillers: tuple[UserStep, ...] = ()
        else:
            first_filler = next((index for index, step in enumerate(before_final)
                                 if step.kind == StepKind.FILLER), len(before_final))
            exposure, fillers = before_final[:first_filler], before_final[first_filler:]
            if not exposure or any(step.kind == StepKind.FINAL_PROBE for step in exposure):
                raise ValueError("Frozen live exposure must precede filler")
            if any(step.kind != StepKind.FILLER for step in fillers):
                raise ValueError("Non-filler step after filler exposure boundary")
        exposure_sha256 = digest(tuple(_step_digest(step) for step in exposure))
        final = plan.steps[-1]
    elif isinstance(plan, ScriptedPlan):
        if assignment.arm != Arm.S or not plan.later_steps or plan.later_steps[-1].kind != StepKind.FINAL_PROBE:
            raise ValueError("S requires scripted exposure and final probe")
        fillers = plan.later_steps[:-1]
        if any(step.kind != StepKind.FILLER for step in fillers):
            raise ValueError("S post-exposure steps must be benign fillers")
        exposure_sha256 = digest((_step_digest(plan.exposure_user),
                                  plan.scripted_assistant.text,
                                  plan.scripted_assistant.label.value,
                                  plan.scripted_assistant.script_version))
        final = plan.later_steps[-1]
    else:
        raise TypeError("Unknown feasibility plan")
    if len(fillers) != (assignment.distance or 0):
        raise ValueError("Planned filler count differs from assigned distance")
    if assignment.arm == Arm.B0 and assignment.distance is not None:
        raise ValueError("B0 distance must remain not applicable")
    return DistanceSchedule(
        trial_id=assignment.trial_id, assigned_distance=assignment.distance,
        exposure_sha256=exposure_sha256,
        filler_step_sha256=tuple(_step_digest(step) for step in fillers),
        final_probe_sha256=_step_digest(final),
        planned_filler_exchanges=len(fillers),
        planned_token_distance=planned_token_distance,
        token_estimator_reference=token_estimator_reference,
        token_control_group_id=token_control_group_id,
    )


def validate_frozen_schedule(plan: LivePlan | ScriptedPlan,
                             schedule: DistanceSchedule) -> None:
    rebuilt = build_distance_schedule(
        plan, planned_token_distance=schedule.planned_token_distance,
        token_estimator_reference=schedule.token_estimator_reference,
        token_control_group_id=schedule.token_control_group_id)
    if rebuilt != schedule:
        raise ValueError("Plan changed after distance schedule was frozen")
