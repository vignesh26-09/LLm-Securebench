"""Deterministically resumable orchestration for controlled trajectories."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from core.experiments.models import (
    AttackDefinition, ControlMatchIdentity, ExperimentalCondition,
    ExperimentalObservation, ExperimentSpecification, ObservationStatus,
    generation_digest, utc_now,
)
from core.experiments.canary import CanaryPolicy, inject_canary, marker_for, verify_canary
from core.experiments.contamination import ContaminationLedgerStore, assess_isolation
from core.inference.contracts import ConversationMessage, ConversationRequest


class ObservationStore:
    """Append-only JSON observation store keyed by deterministic observation ID."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self, observation_id: str) -> dict[str, object] | None:
        path = self.root / f"{observation_id}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def save(self, value: ExperimentalObservation) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{value.observation_id}.json"
        if path.exists():
            raise FileExistsError(f"immutable observation already exists: {value.observation_id}")
        path.write_text(json.dumps(asdict(value), indent=2, sort_keys=True), encoding="utf-8")

    def all(self) -> tuple[ExperimentalObservation, ...]:
        if not self.root.exists():
            return ()
        return tuple(ExperimentalObservation(**_restore_observation(json.loads(path.read_text(encoding="utf-8"))))
                     for path in sorted(self.root.glob("*.json")))


class ExperimentRunner:
    def __init__(self, provider, store: ObservationStore, *, require_locked_preregistration: bool = False) -> None:
        if not callable(getattr(provider, "generate_conversation", None)):
            raise TypeError("provider does not support conversation-aware inference")
        self.provider = provider
        self.store = store
        self.require_locked_preregistration = require_locked_preregistration
        self.ledger = ContaminationLedgerStore(store.root.parent / "contamination-ledger")

    def run(self, spec: ExperimentSpecification, *, force: bool = False) -> tuple[ExperimentalObservation, ...]:
        if self.require_locked_preregistration and not spec.preregistration_id:
            raise ValueError("locked_preregistration_required_before_execution")
        output: list[ExperimentalObservation] = []
        for model in spec.models:
            for repetition in range(spec.repetitions):
                seed = spec.seeds[repetition % len(spec.seeds)]
                run_id = _stable_id(spec.experiment_id, model.name, model.version, repetition, seed)
                for case in spec.cases:
                    output.extend(self._run_case(spec, model, case, run_id, seed, force))
        self._record_isolation_evidence(output)
        return tuple(output)

    def _record_isolation_evidence(self, observations):
        for sequential in observations:
            if sequential.condition is not ExperimentalCondition.SEQUENTIAL_ATTACK or not sequential.attack_instance_id:
                continue
            isolated = next((item for item in observations
                             if item.condition is ExperimentalCondition.ISOLATED_ATTACK
                             and item.run_id == sequential.run_id
                             and item.attack_instance_id == sequential.attack_instance_id), None)
            if isolated is None:
                continue
            record = assess_isolation(
                record_id=_stable_id("isolation", sequential.observation_id, isolated.observation_id),
                sequential_observation_id=sequential.observation_id, isolated_observation_id=isolated.observation_id,
                sequential_conversation_id=sequential.conversation_id, isolated_conversation_id=isolated.conversation_id,
                provider=isolated.provider, sequential_metadata=sequential.provider_metadata,
                isolated_metadata=isolated.provider_metadata)
            self.ledger.save(record)

    def _run_case(self, spec, model, case, run_id, seed, force):
        values: list[ExperimentalObservation] = []
        baseline_messages: list[ConversationMessage] = []
        values.append(self._turn(spec, model, case, run_id, seed, "baseline", baseline_messages,
                                 case.baseline_prompt, ExperimentalCondition.BASELINE, force=force))
        attacks = {item.attack_instance_id: item for item in case.attacks}
        for attack in case.attacks:
            messages: list[ConversationMessage] = []
            values.append(self._turn(spec, model, case, run_id, seed, f"isolated-{attack.attack_instance_id}-baseline",
                                     messages, case.baseline_prompt, ExperimentalCondition.BASELINE,
                                     sequence_id=f"isolated-{attack.attack_instance_id}", force=force))
            values.append(self._turn(spec, model, case, run_id, seed,
                f"isolated-{attack.attack_instance_id}", messages, attack.prompt,
                ExperimentalCondition.ISOLATED_ATTACK, attack=attack,
                sequence_id=f"isolated-{attack.attack_instance_id}", sequence_position=1, force=force))
        for sequence_index, sequence in enumerate(case.sequences, start=1):
            sequence_id = f"{case.evaluation_case_id}-sequence-{sequence_index}"
            messages = []
            values.append(self._turn(spec, model, case, run_id, seed, f"{sequence_id}-baseline", messages,
                                     case.baseline_prompt, ExperimentalCondition.BASELINE,
                                     sequence_id=sequence_id, force=force))
            for position, attack_instance_id in enumerate(sequence, start=1):
                attack = attacks[attack_instance_id]
                values.append(self._turn(spec, model, case, run_id, seed,
                    f"{sequence_id}-{attack_instance_id}", messages, attack.prompt,
                    ExperimentalCondition.SEQUENTIAL_ATTACK, attack=attack,
                    sequence_id=sequence_id, sequence_position=position, force=force))
            for probe_position, prompt in enumerate(case.recovery_probes, start=1):
                values.append(self._turn(spec, model, case, run_id, seed,
                    f"{sequence_id}-recovery-{probe_position}", messages, prompt,
                    ExperimentalCondition.RECOVERY, sequence_id=sequence_id,
                    sequence_position=probe_position, force=force))
        return values

    def _turn(self, spec, model, case, run_id, seed, lane, messages, prompt, condition,
              *, attack: AttackDefinition | None = None, sequence_id=None,
              sequence_position=None, force=False):
        observation_id = _stable_id(run_id, case.evaluation_case_id, lane)
        existing = self.store.load(observation_id)
        if existing is not None and not force:
            restored = ExperimentalObservation(**_restore_observation(existing))
            messages[:] = [ConversationMessage(**item) for item in restored.ordered_messages]
            return restored
        if existing is not None and force:
            raise FileExistsError("force cannot overwrite immutable observations; use a new experiment identity")
        conversation_id = _stable_id(run_id, case.evaluation_case_id, lane.split("-")[0], sequence_id)
        turn_index = 1 + max((item.turn_index for item in messages), default=-1)
        policy = CanaryPolicy(**dict(spec.canary_policy)) if spec.canary_policy else CanaryPolicy()
        prior_marker_ids = _prior_canary_marker_ids(messages, policy.marker_prefix)
        marker_id, marker = marker_for(spec.experiment_id, observation_id, turn_index, prefix=policy.marker_prefix)
        request_prompt = inject_canary(prompt, marker) if policy.enabled else prompt
        user = ConversationMessage("user", request_prompt, turn_index, _stable_id(observation_id, "user"))
        messages.append(user)
        try:
            response = self.provider.generate_conversation(ConversationRequest(
                model, conversation_id, tuple(messages), spec.generation, seed,
                spec.system_prompt, {"experiment_id": spec.experiment_id, "condition": condition.value,
                                     "canary_marker_id": marker_id,
                                     "canary_prior_marker_ids": prior_marker_ids,
                                     "canary_verification_method": policy.verification_method},
            ))
        except Exception as error:
            from core.inference.contracts import ContextValidity
            measurement = spec.measurement
            value = ExperimentalObservation(
                observation_id, spec.experiment_id, run_id, case.evaluation_case_id,
                spec.dataset_id, spec.dataset_version,
                attack.attack_id if attack else None,
                attack.attack_instance_id if attack else None,
                attack.attack_family if attack else None,
                condition, sequence_id, sequence_position, model.name, model.version,
                getattr(self.provider, "provider_name", model.provider), asdict(spec.generation),
                seed, None, False, measurement.behavior_representation_version,
                measurement.layer1_version, measurement.layer2_judge_version,
                measurement.prompt_version, measurement.rubric_version,
                measurement.measurement_version, measurement.threat_model, utc_now(),
                ContextValidity.UNKNOWN, "provider_call_failed", conversation_id, turn_index,
                tuple(asdict(item) for item in messages), None, ObservationStatus.FAILED,
                None, {}, f"{type(error).__name__}: {error}",
                dict(measurement.layer1_configuration), dict(measurement.layer2_judge_configuration),
                dict(measurement.measurement_parameters),
                {"marker_id": marker_id, "marker": marker, "turn_index": turn_index,
                 "prior_marker_ids": prior_marker_ids, "status": "canary_undetermined",
                 "verification_method": policy.verification_method,
                 "reason": "provider_call_failed", "provider_evidence": {}}, spec.preregistration_id)
            self.store.save(value)
            return value
        assistant = ConversationMessage("assistant", response.text, turn_index,
                                        _stable_id(observation_id, "assistant"))
        messages.append(assistant)
        measurement = spec.measurement
        control = None
        if attack is not None:
            control = ControlMatchIdentity(
                case.evaluation_case_id, attack.attack_id, attack.attack_instance_id,
                model.name, model.version, response.provider,
                generation_digest(spec.generation, seed), spec.dataset_version,
                measurement.behavior_representation_version, measurement.layer1_version,
                measurement.layer2_judge_version, measurement.measurement_version,
                measurement.threat_model,
            )
        evidence = verify_canary(marker_id=marker_id, marker=marker, turn_index=turn_index,
                                 prior_marker_ids=prior_marker_ids, metadata=response.metadata, policy=policy)
        value = ExperimentalObservation(
            observation_id, spec.experiment_id, run_id, case.evaluation_case_id,
            spec.dataset_id, spec.dataset_version,
            attack.attack_id if attack else None,
            attack.attack_instance_id if attack else None,
            attack.attack_family if attack else None,
            condition, sequence_id, sequence_position, model.name, model.version,
            response.provider, asdict(spec.generation), response.requested_seed,
            response.effective_seed, response.provider_supports_seed,
            measurement.behavior_representation_version, measurement.layer1_version,
            measurement.layer2_judge_version, measurement.prompt_version,
            measurement.rubric_version, measurement.measurement_version,
            measurement.threat_model, utc_now(), response.context_status,
            str(response.metadata.get("context_reason")) if response.metadata.get("context_reason") else None,
            response.conversation_id, response.turn_index,
            tuple(asdict(item) for item in messages), response.text,
            ObservationStatus.COMPLETED, control, dict(response.metadata), None,
            dict(measurement.layer1_configuration), dict(measurement.layer2_judge_configuration),
            dict(measurement.measurement_parameters),
            {"marker_id": evidence.marker_id, "marker": evidence.marker, "turn_index": evidence.turn_index,
             "prior_marker_ids": evidence.prior_marker_ids, "status": evidence.status.value,
             "verification_method": evidence.verification_method, "reason": evidence.reason,
             "provider_evidence": dict(evidence.provider_evidence)}, spec.preregistration_id,
        )
        self.store.save(value)
        return value


def _stable_id(*parts: object) -> str:
    return hashlib.sha256(":".join(str(part) for part in parts).encode()).hexdigest()[:24]


def _prior_canary_marker_ids(messages, prefix: str) -> tuple[str, ...]:
    pattern = re.compile(rf"<{re.escape(prefix)}:([0-9a-f]{{24}})>")
    return tuple(f"{prefix}-{match.group(1)[:12]}" for item in messages
                 if item.role == "user" for match in pattern.finditer(item.content))


def _restore_observation(value: dict[str, object]) -> dict[str, object]:
    from core.experiments.models import ControlMatchIdentity, ExperimentalCondition, ObservationStatus
    from core.inference.contracts import ContextValidity
    output = dict(value)
    output["condition"] = ExperimentalCondition(output["condition"])
    output["status"] = ObservationStatus(output["status"])
    output["context_status"] = ContextValidity(output["context_status"])
    output["ordered_messages"] = tuple(output["ordered_messages"])
    if output.get("control_identity"):
        output["control_identity"] = ControlMatchIdentity(**output["control_identity"])
    return output
