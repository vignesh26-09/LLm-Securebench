"""Mock-only Phase 4 trajectory runner; real calls require later preflight work."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json

from core.feasibility_pilot.allocation import AllocationLedger, Arm
from core.feasibility_pilot.checker import compute_disclosure_outcome
from core.feasibility_pilot.live_arms import LivePlan, realized_refusal
from core.feasibility_pilot.cases import digest
from core.feasibility_pilot.distance import (DistanceSchedule, build_distance_schedule,
                                             validate_frozen_schedule)
from core.feasibility_pilot.matching import PlannedMatch
from core.feasibility_pilot.observations import AttemptEvent, ObservationLedger
from core.feasibility_pilot.outcomes import DefenderResponse
from core.feasibility_pilot.restricted_store import EvidenceConflict, RestrictedEvidenceStore
from core.feasibility_pilot.scripted_arm import ScriptedPlan, validate_scripted_plan
from core.feasibility_pilot.secrets import SecretAllocator
from core.inference.contracts import (ConversationMessage, ConversationRequest,
                                      GenerationConfig)
from core.models.registry import ModelMetadata


class PreSubmissionFailure(RuntimeError):
    """Provider attests that no request bytes were submitted; one retry allowed."""


def _request_bytes(request: ConversationRequest) -> bytes:
    # Raw system prompt and full history are restricted; metadata is excluded.
    return json.dumps({"model": request.model.name, "conversation_id": request.conversation_id,
                       "system_prompt": request.system_prompt,
                       "messages": [asdict(item) for item in request.messages],
                       "generation": asdict(request.generation), "seed": request.requested_seed},
                      sort_keys=True).encode()


class PilotRunner:
    def __init__(self, *, provider: object, model: ModelMetadata,
                 generation: GenerationConfig, assignments: AllocationLedger,
                 restricted: RestrictedEvidenceStore, observations: ObservationLedger,
                 approved_material: tuple[str, ...], trusted_instruction_template: str,
                 planned_matches: dict[str, PlannedMatch] | None = None,
                 distance_schedules: dict[str, DistanceSchedule] | None = None) -> None:
        # Phase 4 exercises state transitions with mocks. Later phases must
        # implement signed preflight, budget and actual-provider authorization.
        if getattr(provider, "provider_name", None) != "mock":
            raise ValueError("Phase 4 runner permits mock provider only")
        if not assignments.frozen or trusted_instruction_template.count("{secret}") != 1:
            raise ValueError("Frozen assignments and explicit trusted template required")
        if not approved_material or any(not item for item in approved_material):
            raise ValueError("Frozen approved-material corpus required")
        self.provider = provider
        self.model = model
        self.generation = generation
        self.assignments = assignments
        self.restricted = restricted
        self.observations = observations
        self.approved_material = approved_material
        self.trusted_instruction_template = trusted_instruction_template
        self.secrets = SecretAllocator(restricted)
        self.planned_matches = dict(planned_matches or {})
        self.distance_schedules = dict(distance_schedules or {})
        # Freeze the entire denominator before any attempted response.
        observations.freeze_assignments(assignments)

    def _attempt(self, assignment: object, turn_index: int,
                 messages: tuple[ConversationMessage, ...], system_prompt: str):
        trial_id = assignment.trial_id
        request = ConversationRequest(self.model, trial_id, messages, self.generation,
                                      assignment.seed, system_prompt)
        payload = _request_bytes(request)
        for number in (1, 2):
            attempt_id = f"{trial_id}.turn{turn_index}.attempt{number}"
            submitted = self.observations.read_event(attempt_id, "submitted")
            completed = self.observations.read_event(attempt_id, "response")
            prefailed = self.observations.read_event(attempt_id, "pre_submission_failure")
            uncertain = self.observations.read_event(attempt_id, "uncertain_failure")
            if completed is not None:
                reference = completed["response_reference"]
                if reference is None or completed.get("valid_response") is False:
                    return None, {"error_code": "invalid_or_incomplete_response"}
                text = self.restricted.read_raw(reference).decode("utf-8")
                if hashlib.sha256(text.encode()).hexdigest() != completed["response_sha256"]:
                    raise EvidenceConflict("Response evidence hash mismatch")
                if not text.strip() or completed["finish_reason"] not in {"stop", "mock", "eos"}:
                    return None, {"error_code": "invalid_or_incomplete_response"}
                return DefenderResponse(reference, text, True, True,
                                        completed["finish_reason"]), completed
            if uncertain is not None or (submitted is not None and prefailed is None):
                # A crash after submission may have reached the provider.
                return None, {"error_code": "delivery_uncertain_no_retry"}
            if prefailed is not None:
                if number == 1:
                    continue
                return None, {"error_code": "pre_submission_retry_exhausted"}
            request_reference = f"{attempt_id}.request"
            self.restricted.append_raw(request_reference, trial_id, "prompt", payload)
            self.observations.event(AttemptEvent(attempt_id, trial_id, turn_index,
                                                 number, "submitted",
                                                 request_reference=request_reference))
            try:
                response = self.provider.generate_conversation(request)
            except PreSubmissionFailure:
                self.observations.event(AttemptEvent(attempt_id, trial_id, turn_index,
                                                     number, "pre_submission_failure",
                                                     request_reference=request_reference,
                                                     error_code="attested_pre_submission"))
                continue
            except Exception:
                self.observations.event(AttemptEvent(attempt_id, trial_id, turn_index,
                                                     number, "uncertain_failure",
                                                     request_reference=request_reference,
                                                     error_code="provider_or_delivery_uncertain"))
                return None, {"error_code": "provider_or_delivery_uncertain"}
            if (response.conversation_id != trial_id or response.turn_index != messages[-1].turn_index
                    or response.model != self.model
                    or response.provider != self.provider.provider_name):
                self.observations.event(AttemptEvent(attempt_id, trial_id, turn_index,
                                                     number, "uncertain_failure",
                                                     request_reference=request_reference,
                                                     error_code="response_identity_invalid"))
                return None, {"error_code": "response_identity_invalid"}
            text = response.text
            reference = f"{attempt_id}.response" if isinstance(text, str) and text else None
            if reference:
                self.restricted.append_raw(reference, trial_id, "response", text.encode("utf-8"))
            finish = response.finish_reason if response.finish_reason in {
                "stop", "length", "mock", "eos"} else "unknown"
            valid_response = bool(reference and text.strip() and finish in {"stop", "mock", "eos"})
            usage = response.token_usage
            event = self.observations.event(AttemptEvent(
                attempt_id, trial_id, turn_index, number, "response",
                request_reference=request_reference, response_reference=reference,
                response_sha256=hashlib.sha256(text.encode()).hexdigest() if reference else None,
                finish_reason=finish,
                provider_input_tokens=usage.input_tokens if usage else None,
                provider_output_tokens=usage.output_tokens if usage else None,
                valid_response=valid_response))
            if not valid_response:
                return None, {"error_code": "invalid_or_incomplete_response"}
            return DefenderResponse(reference, text, True, True, finish), event
        return None, {"error_code": "pre_submission_retry_exhausted"}

    def run(self, plan: LivePlan | ScriptedPlan) -> dict:
        assignment = plan.assignment
        if self.assignments.get(assignment.trial_id) != assignment:
            raise EvidenceConflict("Plan differs from frozen allocation")
        if assignment.model_id != self.model.name:
            raise ValueError("Allocation model mismatch")
        if isinstance(plan, ScriptedPlan):
            validate_scripted_plan(plan, self.restricted)
        elif not isinstance(plan, LivePlan) or assignment.arm == Arm.S:
            raise ValueError("Arm/plan mechanism mismatch")
        schedule = self.distance_schedules.get(assignment.trial_id)
        if schedule is None:
            schedule = build_distance_schedule(plan)
        else:
            validate_frozen_schedule(plan, schedule)
        self.observations.assign(assignment)
        self.observations.freeze_distance_schedule(schedule)
        plan_sha256 = digest(asdict(plan))
        prior = self.observations.observation(assignment.trial_id)
        if prior is not None:
            if prior["plan_sha256"] != plan_sha256:
                raise EvidenceConflict("Completed plan differs from immutable evidence")
            return prior
        binding = self.secrets.bind(assignment.trial_id, self.approved_material)
        secret = self.secrets.read_for_restricted_checker(binding)
        system_prompt = self.trusted_instruction_template.format(secret=secret)
        messages: list[ConversationMessage] = []
        responses: list[DefenderResponse] = []
        event_rows: list[dict] = []
        refusal_count = 0
        complete_filler_exchanges = 0
        steps = plan.steps if isinstance(plan, LivePlan) else (plan.exposure_user,) + plan.later_steps
        for step in steps:
            self.restricted.assert_public_safe(step.text)
        for step_number, step in enumerate(steps):
            turn_index = len(messages)
            messages.append(ConversationMessage("user", step.text, turn_index,
                                                f"{assignment.trial_id}.user{step_number}"))
            if isinstance(plan, ScriptedPlan) and step_number == 0:
                # Only S may contain a scripted assistant; it is never an
                # eligible defender response for Y_earlier.
                scripted = plan.scripted_assistant
                messages.append(ConversationMessage("assistant", scripted.text, len(messages),
                                                    f"{assignment.trial_id}.scripted"))
                continue
            response, event = self._attempt(assignment, step_number,
                                            tuple(messages), system_prompt)
            event_rows.append(event)
            if response is None:
                outcome = compute_disclosure_outcome(secret, None, responses,
                                                     trajectory_complete=False)
                return self._seal(assignment, "incomplete", outcome, refusal_count,
                                  event_rows, event.get("error_code"), plan_sha256,
                                  schedule, complete_filler_exchanges)
            responses.append(response)
            if step.kind.value == "filler":
                complete_filler_exchanges += 1
            refusal_count += int(realized_refusal(response.text or ""))
            messages.append(ConversationMessage("assistant", response.text or "",
                                                len(messages), response.response_id))
        outcome = compute_disclosure_outcome(secret, responses[-1], responses[:-1],
                                             trajectory_complete=True)
        return self._seal(assignment, "completed" if outcome.status == "computed" else "invalid",
                          outcome, refusal_count, event_rows, outcome.reason, plan_sha256,
                          schedule, complete_filler_exchanges)

    def _seal(self, assignment: object, status: str, outcome: object,
              refusals: int, events: list[dict], reason: str | None,
              plan_sha256: str, schedule: DistanceSchedule,
              complete_filler_exchanges: int) -> dict:
        # Public record contains no raw text or unkeyed secret digest.
        row = {"trial_id": assignment.trial_id, "assignment_sha256":
               self.observations.assign(assignment)["content_sha256"],
               "plan_sha256": plan_sha256,
               "arm": assignment.arm.value, "distance": assignment.distance,
               "matching_set_id": assignment.matching_set_id,
               "evidence_class": assignment.evidence_class,
               "execution_provenance": "mock_fixture",
               "live_primary_eligible_arm": assignment.live_primary_eligible_arm,
               "status": status, "reason": reason,
               "distance_schedule_sha256": schedule.content_sha256,
               "planned_filler_exchanges": schedule.planned_filler_exchanges,
               "realized_complete_filler_exchanges": complete_filler_exchanges,
               "attempt_event_hashes": [item["content_sha256"] for item in events
                                        if "content_sha256" in item],
               "realized_refusals": refusals,
               "provider_input_tokens": sum(item.get("provider_input_tokens") or 0 for item in events),
               "provider_output_tokens": sum(item.get("provider_output_tokens") or 0 for item in events),
               "planned_matching_status": (
                   "matched" if self.planned_matches[assignment.trial_id].matched else "mismatched"
                   ) if assignment.trial_id in self.planned_matches else "not_audited",
               "planned_matching_reasons": list(self.planned_matches[assignment.trial_id].reasons)
                   if assignment.trial_id in self.planned_matches else [],
               "realized_matching_status": "descriptive_only",
               "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
               "outcome_status": outcome.status, "checker_version": outcome.checker_version,
               "y_final": outcome.y_final, "y_earlier": outcome.y_earlier,
               "y_ever": outcome.y_ever,
               "earlier_exact_observed_in_partial_trajectory":
                   outcome.earlier_exact_observed_in_partial_trajectory,
               "final_response_sha256": outcome.final_response_sha256,
               "earlier_response_sha256": list(outcome.earlier_response_sha256)}
        return self.observations.complete(assignment.trial_id, row)
