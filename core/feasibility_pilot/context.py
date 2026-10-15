"""Scientific context evidence, separate from request-level inference status."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.feasibility_pilot.allocation import AllocationLedger, TrialAssignment
    from core.feasibility_pilot.distance import DistanceSchedule
    from core.feasibility_pilot.live_arms import LivePlan
    from core.feasibility_pilot.observations import ObservationLedger
    from core.feasibility_pilot.scripted_arm import ScriptedPlan
    from core.models.registry import ModelMetadata


class ScientificContextStatus(StrEnum):
    RETAINED_VERIFIED = "retained_verified"
    TRUNCATED_KNOWN = "truncated_known"
    RETENTION_UNVERIFIABLE = "retention_unverifiable"


@dataclass(frozen=True, slots=True)
class ContextEvidence:
    """Claims about the *post-template* required content at the final probe.

    Counts, request delivery and canaries may be recorded elsewhere, but are
    deliberately insufficient to set either affirmative field here.
    """

    rendered_prompt_contains_required_content: bool | None = None
    effective_retention_confirmed: bool | None = None
    required_content_known_lost: bool = False
    effective_context_limit_exceeded: bool = False
    evidence_reference: str | None = None


@dataclass(frozen=True, slots=True)
class ContextAssessment:
    status: ScientificContextStatus
    reason: str
    evidence_reference: str | None


def assess_context(evidence: ContextEvidence) -> ContextAssessment:
    """Require affirmative content and retention evidence before verification."""
    if evidence.required_content_known_lost or evidence.effective_context_limit_exceeded:
        reason = ("required_content_known_lost" if evidence.required_content_known_lost
                  else "effective_context_limit_exceeded")
        return ContextAssessment(ScientificContextStatus.TRUNCATED_KNOWN, reason,
                                 evidence.evidence_reference)
    if (evidence.rendered_prompt_contains_required_content is True
            and evidence.effective_retention_confirmed is True
            and evidence.evidence_reference):
        return ContextAssessment(ScientificContextStatus.RETAINED_VERIFIED,
                                 "post_template_content_and_retention_confirmed",
                                 evidence.evidence_reference)
    return ContextAssessment(ScientificContextStatus.RETENTION_UNVERIFIABLE,
                             "post_template_or_effective_retention_evidence_missing",
                             evidence.evidence_reference)


def pair_validity_warning(adversarial: ContextAssessment,
                          topic_control: ContextAssessment) -> bool:
    """Expose asymmetric A/T validity; never silently rematch assignments."""
    return adversarial.status != topic_control.status


@dataclass(frozen=True, slots=True)
class TrialContextAudit:
    trial_id: str
    assignment_sha256: str
    observation_sha256: str | None
    distance_schedule_sha256: str
    model_id: str
    model_digest_recorded: str | None
    template_sha256_recorded: str | None
    model_identity_basis: str
    requested_num_ctx: int | None
    final_provider_input_tokens: int | None
    final_provider_output_tokens: int | None
    total_provider_input_tokens: int | None
    total_provider_output_tokens: int | None
    planned_filler_exchanges: int
    realized_complete_filler_exchanges: int
    planned_token_distance: int | None
    token_estimator_reference: str | None
    observed_token_distance_proxy: int | None
    observed_token_distance_method: str
    rendering_status: str
    trusted_priority_status: str
    scientific_context_status: ScientificContextStatus
    scientific_context_reason: str
    context_evidence_reference: str | None
    verified_context_primary_eligible: bool
    contextual_decay_claim_available: bool
    evidence_class: str = "mock_fixture"
    audit_version: str = "distance-context-audit-v1"


def _valid_response_event(ledger: "ObservationLedger", trial_id: str,
                          step_index: int) -> dict | None:
    for attempt in (1, 2):
        event = ledger.read_event(f"{trial_id}.turn{step_index}.attempt{attempt}", "response")
        if event is not None and event.get("valid_response") is True:
            return event
    return None


def audit_trial_context(*, ledger: "ObservationLedger", assignment: "TrialAssignment",
                        plan: "LivePlan | ScriptedPlan", schedule: "DistanceSchedule",
                        model: "ModelMetadata", evidence: ContextEvidence | None = None) -> TrialContextAudit:
    """Audit saved mock observations; request/token/canary evidence never proves retention."""
    from core.feasibility_pilot.allocation import Arm
    from core.feasibility_pilot.live_arms import LivePlan, StepKind
    from core.feasibility_pilot.distance import validate_frozen_schedule

    validate_frozen_schedule(plan, schedule)
    if assignment != plan.assignment or assignment.model_id != model.name:
        raise ValueError("Context audit identity differs from frozen plan")
    stored_schedule = ledger.distance_schedule(assignment.trial_id)
    if stored_schedule is None or stored_schedule["content_sha256"] != schedule.content_sha256:
        raise ValueError("Context audit lacks frozen schedule evidence")
    assignment_record = ledger._read(Path("assignments") / f"{assignment.trial_id}.json")
    observation = ledger.observation(assignment.trial_id)
    steps = plan.steps if isinstance(plan, LivePlan) else (plan.exposure_user,) + plan.later_steps
    final_event = _valid_response_event(ledger, assignment.trial_id, len(steps) - 1)
    exposure_index = None
    if isinstance(plan, LivePlan) and assignment.arm != Arm.B0:
        exposure_indexes = [index for index, step in enumerate(steps[:-1])
                            if step.kind != StepKind.FILLER]
        exposure_index = exposure_indexes[-1] if exposure_indexes else None
    exposure_event = (_valid_response_event(ledger, assignment.trial_id, exposure_index)
                      if exposure_index is not None else None)
    final_tokens = final_event.get("provider_input_tokens") if final_event else None
    final_output_tokens = final_event.get("provider_output_tokens") if final_event else None
    exposure_tokens = exposure_event.get("provider_input_tokens") if exposure_event else None
    observed_proxy = (final_tokens - exposure_tokens
                      if isinstance(final_tokens, int) and isinstance(exposure_tokens, int)
                      else None)
    assessment = assess_context(evidence or ContextEvidence())
    if assessment.status == ScientificContextStatus.RETAINED_VERIFIED:
        # Phase 5 runner is mock-only; a synthetic assertion is not effective
        # post-template retention proof for an actual local model.
        assessment = ContextAssessment(ScientificContextStatus.RETENTION_UNVERIFIABLE,
                                       "mock_evidence_cannot_verify_effective_retention",
                                       assessment.evidence_reference)
    elif (assessment.status == ScientificContextStatus.TRUNCATED_KNOWN
          and not assessment.evidence_reference):
        assessment = ContextAssessment(ScientificContextStatus.RETENTION_UNVERIFIABLE,
                                       "known_loss_assertion_lacks_evidence_reference", None)
    if model.name.startswith("qwen3.5:"):
        rendering, priority = "rendered_prompt_unverified", "trusted_priority_unverified"
    elif model.name.startswith("gemma3:"):
        rendering, priority = "rendered_prompt_unverified", "trusted_priority_unverified_system_to_user"
    else:
        rendering, priority = "not_assessed", "not_assessed"
    template = model.metadata.get("template_sha256")
    template = template if isinstance(template, str) else None
    complete = observation is not None and observation["status"] == "completed"
    eligible = (complete and assignment.arm in {Arm.A, Arm.T}
                and assessment.status == ScientificContextStatus.RETAINED_VERIFIED)
    return TrialContextAudit(
        trial_id=assignment.trial_id,
        assignment_sha256=assignment_record["content_sha256"],
        observation_sha256=observation["content_sha256"] if observation else None,
        distance_schedule_sha256=schedule.content_sha256,
        model_id=model.name, model_digest_recorded=model.version,
        template_sha256_recorded=template,
        model_identity_basis="request_metadata_only_not_provider_verified",
        requested_num_ctx=model.context_window,
        final_provider_input_tokens=final_tokens,
        final_provider_output_tokens=final_output_tokens,
        total_provider_input_tokens=(observation["provider_input_tokens"] if observation else None),
        total_provider_output_tokens=(observation["provider_output_tokens"] if observation else None),
        planned_filler_exchanges=schedule.planned_filler_exchanges,
        realized_complete_filler_exchanges=(observation["realized_complete_filler_exchanges"]
                                              if observation else 0),
        planned_token_distance=schedule.planned_token_distance,
        token_estimator_reference=schedule.token_estimator_reference,
        observed_token_distance_proxy=observed_proxy,
        observed_token_distance_method="final_minus_exposure_prompt_count_proxy_includes_probe",
        rendering_status=rendering, trusted_priority_status=priority,
        scientific_context_status=assessment.status,
        scientific_context_reason=assessment.reason,
        context_evidence_reference=assessment.evidence_reference,
        verified_context_primary_eligible=eligible,
        contextual_decay_claim_available=False,
    )


@dataclass(frozen=True, slots=True)
class PairContextRow:
    matching_set_id: str
    a_trial_id: str
    t_trial_id: str
    a_status: str
    t_status: str
    a_verified_context_eligible: bool
    t_verified_context_eligible: bool
    a_audit_available: bool
    t_audit_available: bool
    a_completed: bool
    t_completed: bool
    validity_asymmetry: bool


@dataclass(frozen=True, slots=True)
class PairContextReport:
    assigned_pairs: int
    rows: tuple[PairContextRow, ...]
    a_truncated_known: int
    t_truncated_known: int
    a_retention_unverifiable: int
    t_retention_unverifiable: int
    missing_context_audits: int
    completion_asymmetric_pairs: int
    asymmetric_pairs: int
    differential_validity_warning: bool


def report_at_context_pairs(assignments: "AllocationLedger",
                            ledger: "ObservationLedger") -> PairContextReport:
    """Keep every assigned A/T counterpart, even without an audit or outcome."""
    from core.feasibility_pilot.allocation import Arm
    ledger.coverage()
    pairs: dict[str, dict[Arm, object]] = {}
    for assignment in assignments.assignments:
        if assignment.arm in {Arm.A, Arm.T}:
            pairs.setdefault(assignment.matching_set_id, {})[assignment.arm] = assignment
    rows = []
    for pair_id in sorted(pairs):
        pair = pairs[pair_id]
        if set(pair) != {Arm.A, Arm.T}:
            raise ValueError("Frozen A/T pair is incomplete")
        a, t = pair[Arm.A], pair[Arm.T]
        a_audit, t_audit = ledger.context_audit(a.trial_id), ledger.context_audit(t.trial_id)
        a_observation, t_observation = ledger.observation(a.trial_id), ledger.observation(t.trial_id)
        a_completed = bool(a_observation and a_observation["status"] == "completed")
        t_completed = bool(t_observation and t_observation["status"] == "completed")
        a_status = (a_audit["scientific_context_status"] if a_audit else
                    ScientificContextStatus.RETENTION_UNVERIFIABLE.value)
        t_status = (t_audit["scientific_context_status"] if t_audit else
                    ScientificContextStatus.RETENTION_UNVERIFIABLE.value)
        rows.append(PairContextRow(pair_id, a.trial_id, t.trial_id, a_status, t_status,
                                   bool(a_audit and a_audit["verified_context_primary_eligible"]),
                                   bool(t_audit and t_audit["verified_context_primary_eligible"]),
                                   a_audit is not None, t_audit is not None,
                                   a_completed, t_completed,
                                   a_status != t_status or a_completed != t_completed
                                   or (a_audit is None) != (t_audit is None)))
    a_truncated = sum(row.a_status == ScientificContextStatus.TRUNCATED_KNOWN for row in rows)
    t_truncated = sum(row.t_status == ScientificContextStatus.TRUNCATED_KNOWN for row in rows)
    a_unverifiable = sum(row.a_status == ScientificContextStatus.RETENTION_UNVERIFIABLE for row in rows)
    t_unverifiable = sum(row.t_status == ScientificContextStatus.RETENTION_UNVERIFIABLE for row in rows)
    missing_audits = sum(not row.a_audit_available for row in rows) + sum(
        not row.t_audit_available for row in rows)
    completion_asymmetric = sum(row.a_completed != row.t_completed for row in rows)
    asymmetric = sum(row.validity_asymmetry for row in rows)
    return PairContextReport(len(rows), tuple(rows), a_truncated, t_truncated,
                             a_unverifiable, t_unverifiable, missing_audits,
                             completion_asymmetric, asymmetric,
                             bool(asymmetric or a_truncated != t_truncated
                                  or a_unverifiable != t_unverifiable))
