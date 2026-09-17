"""Immutable contracts for controlled trajectory experiments."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Mapping

from core.inference.contracts import ContextValidity, GenerationConfig
from core.models.registry import ModelMetadata


class ExperimentalCondition(StrEnum):
    BASELINE = "baseline"
    ISOLATED_ATTACK = "isolated_attack"
    SEQUENTIAL_ATTACK = "sequential_attack"
    RECOVERY = "recovery"


class ObservationStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class AttackDefinition:
    attack_id: str
    attack_instance_id: str
    attack_family: str
    prompt: str

    def __post_init__(self) -> None:
        if not all((self.attack_id, self.attack_instance_id, self.attack_family, self.prompt)):
            raise ValueError("attack definition fields are required")


@dataclass(frozen=True, slots=True)
class EvaluationCaseDesign:
    evaluation_case_id: str
    baseline_prompt: str
    attacks: tuple[AttackDefinition, ...]
    sequences: tuple[tuple[str, ...], ...]
    recovery_probes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        known = {item.attack_instance_id for item in self.attacks}
        if not self.evaluation_case_id or not self.baseline_prompt:
            raise ValueError("case identity and baseline prompt are required")
        if len(known) != len(self.attacks):
            raise ValueError("attack instance identities must be unique within a case")
        if any(not sequence or not set(sequence) <= known for sequence in self.sequences):
            raise ValueError("sequences must reference declared attack instances")


@dataclass(frozen=True, slots=True)
class MeasurementConfiguration:
    behavior_representation_version: str
    layer1_version: str | None
    layer2_judge_version: str | None
    prompt_version: str
    rubric_version: str | None
    measurement_version: str
    threat_model: str
    layer1_configuration: Mapping[str, object] = field(default_factory=dict)
    layer2_judge_configuration: Mapping[str, object] = field(default_factory=dict)
    measurement_parameters: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExperimentSpecification:
    experiment_id: str
    dataset_id: str
    dataset_version: str
    dataset_hash: str
    models: tuple[ModelMetadata, ...]
    cases: tuple[EvaluationCaseDesign, ...]
    generation: GenerationConfig
    seeds: tuple[int, ...]
    repetitions: int
    measurement: MeasurementConfiguration
    system_prompt: str | None = None
    specification_version: str = "controlled-trajectory-v1"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.experiment_id, self.dataset_id, self.dataset_version, self.dataset_hash)):
            raise ValueError("experiment and dataset identity are required")
        if not self.models or not self.cases or not self.seeds or self.repetitions <= 0:
            raise ValueError("models, cases, seeds, and positive repetitions are required")


@dataclass(frozen=True, slots=True)
class ControlMatchIdentity:
    evaluation_case_id: str
    attack_id: str
    attack_instance_id: str
    target_model: str
    target_model_version: str | None
    provider: str
    generation_digest: str
    dataset_version: str
    behavior_representation_version: str
    layer1_version: str | None
    layer2_judge_version: str | None
    measurement_version: str
    threat_model: str


@dataclass(frozen=True, slots=True)
class ControlMatchResult:
    matched: bool
    reason: str | None = None


def validate_control_match(sequential: ControlMatchIdentity, isolated: ControlMatchIdentity) -> ControlMatchResult:
    checks = (
        ("control_case_mismatch", "evaluation_case_id"),
        ("control_attack_mismatch", "attack_id"),
        ("control_attack_instance_mismatch", "attack_instance_id"),
        ("control_model_mismatch", "target_model"),
        ("control_model_version_mismatch", "target_model_version"),
        ("control_provider_mismatch", "provider"),
        ("control_generation_mismatch", "generation_digest"),
        ("control_dataset_mismatch", "dataset_version"),
        ("control_behavior_representation_mismatch", "behavior_representation_version"),
        ("control_layer1_mismatch", "layer1_version"),
        ("control_judge_mismatch", "layer2_judge_version"),
        ("control_measurement_mismatch", "measurement_version"),
        ("control_threat_model_mismatch", "threat_model"),
    )
    for reason, field_name in checks:
        if getattr(sequential, field_name) != getattr(isolated, field_name):
            return ControlMatchResult(False, reason)
    return ControlMatchResult(True)


@dataclass(frozen=True, slots=True)
class ExperimentalObservation:
    observation_id: str
    experiment_id: str
    run_id: str
    evaluation_case_id: str
    dataset_id: str
    dataset_version: str
    attack_id: str | None
    attack_instance_id: str | None
    attack_family: str | None
    condition: ExperimentalCondition
    sequence_id: str | None
    sequence_position: int | None
    target_model: str
    target_model_version: str | None
    provider: str
    generation_configuration: Mapping[str, object]
    requested_seed: int | None
    effective_seed: int | None
    provider_supports_seed: bool
    behavior_representation_version: str
    layer1_version: str | None
    layer2_judge_version: str | None
    prompt_version: str
    rubric_version: str | None
    measurement_version: str
    threat_model: str
    timestamp: str
    context_status: ContextValidity
    context_reason: str | None
    conversation_id: str
    turn_index: int
    ordered_messages: tuple[Mapping[str, object], ...]
    response: str | None
    status: ObservationStatus
    control_identity: ControlMatchIdentity | None = None
    provider_metadata: Mapping[str, object] = field(default_factory=dict)
    reason: str | None = None
    layer1_configuration: Mapping[str, object] = field(default_factory=dict)
    layer2_judge_configuration: Mapping[str, object] = field(default_factory=dict)
    measurement_parameters: Mapping[str, object] = field(default_factory=dict)


def generation_digest(config: GenerationConfig, seed: int | None) -> str:
    payload = {**asdict(config), "requested_seed": seed}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
