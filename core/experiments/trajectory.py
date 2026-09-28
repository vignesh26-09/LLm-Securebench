"""Bind independently measured behavior to controlled observations for RC/SAEA.

This adapter deliberately does not score model text. Callers must supply a
versioned behavioral measurement (for example, from a separately configured
Layer 2 service). Missing measurements remain failed/unavailable states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from core.experiments.models import ExperimentalCondition, ExperimentalObservation
from core.experiments.canary import CanaryStatus
from core.experiments.contamination import SessionContaminationRecord
from core.recovery.models import (BehavioralState as RCState, RCContextStatus,
    RCResultStatus, RecoveryRunInput, RecoveryStep)
from core.saea.models import (AttackInstance, BehavioralState, ContextStatus,
    ResultStatus, SAEAInput, SpacingCondition)


@dataclass(frozen=True, slots=True)
class BehaviorMeasurement:
    observation_id: str
    scores: Mapping[str, float]
    behavior_representation_version: str
    source: str
    status: ResultStatus = ResultStatus.APPLICABLE
    reason: str | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)


def build_saea_input(observations: Sequence[ExperimentalObservation],
                     measurements: Sequence[BehaviorMeasurement], *,
                     sequence_id: str, run_id: str | None = None,
                     contamination_records: Sequence[SessionContaminationRecord] = ()) -> SAEAInput:
    ordered = tuple(item for item in observations if item.sequence_id == sequence_id)
    if not ordered:
        raise ValueError("sequence observations are unavailable")
    baseline = _one(item for item in ordered if item.condition is ExperimentalCondition.BASELINE)
    sequential = tuple(sorted((item for item in ordered if item.condition is ExperimentalCondition.SEQUENTIAL_ATTACK),
                              key=lambda item: item.sequence_position or 0))
    if baseline is None or not sequential:
        raise ValueError("sequence requires a baseline and at least one sequential attack")
    index = {item.observation_id: item for item in measurements}
    contamination_index = {(item.sequential_observation_id, item.isolated_observation_id): item
                           for item in contamination_records}
    states = {item.observation_id: _saea_state(item, index.get(item.observation_id)) for item in observations}
    attacks = []
    for item in sequential:
        isolated = _one(candidate for candidate in observations
                        if candidate.condition is ExperimentalCondition.ISOLATED_ATTACK
                        and candidate.attack_instance_id == item.attack_instance_id
                        and candidate.run_id == item.run_id)
        isolated_baseline = _one(candidate for candidate in observations
                                 if candidate.condition is ExperimentalCondition.BASELINE
                                 and candidate.sequence_id == f"isolated-{item.attack_instance_id}"
                                 and candidate.run_id == item.run_id)
        contamination = contamination_index.get((item.observation_id, isolated.observation_id)) if isolated else None
        attacks.append(AttackInstance(
            item.attack_instance_id or "missing", item.attack_id or "missing", item.attack_family or "missing",
            item.attack_family or "missing", item.sequence_position or 0, item.evaluation_case_id,
            states[item.observation_id], states[isolated.observation_id] if isolated else None,
            (states[isolated_baseline.observation_id],) if isolated_baseline else (),
            sequential_identity=item.control_identity,
            isolated_identity=isolated.control_identity if isolated else None,
            metadata={"sequential_observation_id": item.observation_id,
                      "isolated_observation_id": isolated.observation_id if isolated else None,
                      "contamination_record_id": contamination.record_id if contamination else None},
            contamination_status=contamination.status.value if contamination else None,
        ))
    return SAEAInput(
        run_id or baseline.run_id, sequence_id, baseline.target_model, baseline.dataset_id,
        baseline.dataset_version, (states[baseline.observation_id],), tuple(attacks),
        SpacingCondition.STACKED, _saea_context(ordered),
        metadata={"controlled_observation_ids": tuple(item.observation_id for item in ordered),
                  "measurement_sources": {item.observation_id: index[item.observation_id].source
                                          for item in ordered if item.observation_id in index},
                  "context_gate": _context_gate_metadata(ordered)},
    )


def build_recovery_input(observations: Sequence[ExperimentalObservation],
                         measurements: Sequence[BehaviorMeasurement], *,
                         sequence_id: str, attack_position: int | None = None,
                         run_id: str | None = None) -> RecoveryRunInput:
    ordered = tuple(item for item in observations if item.sequence_id == sequence_id)
    baseline = _one(item for item in ordered if item.condition is ExperimentalCondition.BASELINE)
    sequential = tuple(sorted((item for item in ordered if item.condition is ExperimentalCondition.SEQUENTIAL_ATTACK),
                              key=lambda item: item.sequence_position or 0))
    recovery = tuple(sorted((item for item in ordered if item.condition is ExperimentalCondition.RECOVERY),
                            key=lambda item: item.sequence_position or 0))
    if baseline is None or not sequential or not recovery:
        raise ValueError("recovery requires baseline, sequential attack, and recovery observations")
    attack = sequential[-1] if attack_position is None else _one(item for item in sequential if item.sequence_position == attack_position)
    if attack is None:
        raise ValueError("requested attack position is unavailable")
    index = {item.observation_id: item for item in measurements}
    return RecoveryRunInput(
        run_id or baseline.run_id, baseline.target_model, baseline.conversation_id,
        (_rc_state(baseline, index.get(baseline.observation_id)),),
        _rc_state(attack, index.get(attack.observation_id)),
        tuple(RecoveryStep(position, _rc_state(item, index.get(item.observation_id)))
              for position, item in enumerate(recovery, start=1)),
        context_status=_rc_context(ordered),
        generation_config=dict(baseline.generation_configuration),
        provenance={"controlled_sequence_id": sequence_id,
                    "measurement_sources": {item.observation_id: index[item.observation_id].source
                                            for item in ordered if item.observation_id in index},
                    "context_gate": _context_gate_metadata(ordered)},
    )


def _saea_state(observation, measurement):
    if measurement is None:
        return BehavioralState(observation.observation_id, {}, ResultStatus.FAILED_EVALUATION,
                               "behavior_measurement_unavailable", {"observation_id": observation.observation_id})
    return BehavioralState(observation.observation_id, dict(measurement.scores), measurement.status,
                           measurement.reason, {"source": measurement.source, **dict(measurement.provenance)})


def _rc_state(observation, measurement):
    if measurement is None:
        return RCState(observation.observation_id, {}, status=RCResultStatus.FAILED_EVALUATION,
                       reason="behavior_measurement_unavailable", provenance={"observation_id": observation.observation_id})
    return RCState(observation.observation_id, dict(measurement.scores),
                   status=RCResultStatus.APPLICABLE if measurement.status is ResultStatus.APPLICABLE else RCResultStatus.FAILED_EVALUATION,
                   reason=measurement.reason, provenance={"source": measurement.source, **dict(measurement.provenance)})


def _saea_context(observations):
    from core.inference.contracts import ContextValidity
    if _has_failed_canary(observations):
        return ContextStatus.TRUNCATED
    states = {item.context_status for item in observations}
    if ContextValidity.TRUNCATED in states:
        return ContextStatus.TRUNCATED
    return ContextStatus.RETAINED if states == {ContextValidity.RETAINED} else ContextStatus.UNKNOWN


def _rc_context(observations):
    from core.inference.contracts import ContextValidity
    if _has_failed_canary(observations):
        return RCContextStatus.TRUNCATED
    states = {item.context_status for item in observations}
    if ContextValidity.TRUNCATED in states:
        return RCContextStatus.TRUNCATED
    return RCContextStatus.RETAINED if states == {ContextValidity.RETAINED} else RCContextStatus.UNKNOWN


def _has_failed_canary(observations) -> bool:
    return any((item.canary_evidence or {}).get("status") == CanaryStatus.FAILED.value for item in observations)


def _context_gate_metadata(observations) -> dict[str, object]:
    statuses = tuple((item.canary_evidence or {}).get("status", CanaryStatus.NOT_APPLICABLE.value)
                     for item in observations)
    return {"provider_context_states": tuple(item.context_status.value for item in observations),
            "canary_statuses": statuses,
            "canary_failure_blocks_metrics": _has_failed_canary(observations),
            "preferred_evidence": "canary_verified" if CanaryStatus.VERIFIED.value in statuses
                                  else "provider_context_declaration",
            "note": "canary verification is request-level evidence and does not promote an unknown provider context state"}


def _one(values):
    items = tuple(values)
    return items[0] if len(items) == 1 else None
