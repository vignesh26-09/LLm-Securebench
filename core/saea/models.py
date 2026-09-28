"""Machine-readable, provider-neutral SAEA input and output contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from core.experiments.models import ControlMatchIdentity


REQUIRED_DIMENSIONS = frozenset({"safety", "helpfulness"})
METHODOLOGY_VERSION = "saea-reconciled-v1"


class ResultStatus(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNDEFINED = "undefined"
    INSUFFICIENT_DATA = "insufficient_data"
    CALIBRATION_UNAVAILABLE = "calibration_unavailable"
    FAILED_EVALUATION = "failed_evaluation"


class ContextStatus(StrEnum):
    RETAINED = "retained"
    TRUNCATED = "truncated"
    UNKNOWN = "unknown"
    RESET = "reset"


class SpacingCondition(StrEnum):
    STACKED = "stacked"
    SPACED = "spaced"


@dataclass(frozen=True, slots=True)
class BehavioralState:
    state_id: str
    scores: Mapping[str, float] = field(default_factory=dict)
    status: ResultStatus = ResultStatus.APPLICABLE
    reason: str | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for dimension, score in self.scores.items():
            if not dimension or isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0.0 <= score <= 1.0:
                raise ValueError("behavioral state scores must be finite values in [0, 1]")


@dataclass(frozen=True, slots=True)
class RecoveryWindow:
    after_position: int
    rc_auc_raw: float | None
    applicability: ResultStatus
    reason: str | None = None
    rc_result_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.after_position <= 0:
            raise ValueError("recovery window position must be positive")
        if self.rc_auc_raw is not None and (isinstance(self.rc_auc_raw, bool) or not math.isfinite(self.rc_auc_raw)):
            raise ValueError("rc_auc_raw must be finite when supplied")


@dataclass(frozen=True, slots=True)
class AttackInstance:
    attack_instance_id: str
    attack_id: str
    category: str
    technique_family: str
    position: int
    evaluation_case_id: str
    state: BehavioralState
    isolated_state: BehavioralState | None
    isolated_baseline: tuple[BehavioralState, ...] = ()
    bsda_reference: Mapping[str, object] | None = None
    recovery_window: RecoveryWindow | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    sequential_identity: ControlMatchIdentity | None = None
    isolated_identity: ControlMatchIdentity | None = None
    contamination_status: str | None = None

    def __post_init__(self) -> None:
        if not self.attack_instance_id or not self.attack_id or self.position <= 0:
            raise ValueError("attack instances require IDs and a positive position")


@dataclass(frozen=True, slots=True)
class CoalitionEvaluation:
    """Pre-generated coalition trajectory result in original sequence order."""
    attack_instance_ids: frozenset[str]
    cumulative_vulnerability: float | None
    status: ResultStatus = ResultStatus.APPLICABLE
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SAEAConfig:
    methodology_version: str = METHODOLOGY_VERSION
    calibration_artifact_id: str | None = None
    near_zero_bliss_threshold: float | None = None
    bootstrap_resamples: int = 1000
    bootstrap_confidence: float = 0.95
    random_seed: int = 0
    shapley_target_standard_error: float | None = None

    def __post_init__(self) -> None:
        if self.near_zero_bliss_threshold is not None:
            if self.calibration_artifact_id is None or not math.isfinite(self.near_zero_bliss_threshold) or self.near_zero_bliss_threshold < 0:
                raise ValueError("a finite near-zero threshold requires a calibration artifact")
        if self.bootstrap_resamples <= 0 or not 0.0 < self.bootstrap_confidence < 1.0:
            raise ValueError("bootstrap configuration is invalid")
        if self.shapley_target_standard_error is not None and (not math.isfinite(self.shapley_target_standard_error) or self.shapley_target_standard_error <= 0):
            raise ValueError("Shapley target standard error must be positive and finite")


@dataclass(frozen=True, slots=True)
class SAEAInput:
    run_id: str
    sequence_id: str
    model_id: str
    dataset_id: str
    dataset_version: str | None
    baseline_states: tuple[BehavioralState, ...]
    attacks: tuple[AttackInstance, ...]
    spacing: SpacingCondition
    context_status: ContextStatus
    config: SAEAConfig = field(default_factory=SAEAConfig)
    coalition_evaluations: tuple[CoalitionEvaluation, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StateTransition:
    position: int
    attack_instance_id: str
    baseline_vector: Mapping[str, float] | None
    state_vector: Mapping[str, float] | None
    delta: float | None
    status: ResultStatus
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PerStepVulnerability:
    position: int
    attack_instance_id: str
    delta: float | None
    isolated_delta: float | None
    context_effect: float | None
    status: ResultStatus
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SequentialTrajectory:
    transitions: tuple[StateTransition, ...]
    cumulative_vulnerability: float | None
    status: ResultStatus
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SynergyResult:
    observed_cumulative_vulnerability: float | None
    bliss_expected_effect: float | None
    synergy_index: float | None
    status: ResultStatus
    reason: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ShapleyAttributionResult:
    values: Mapping[str, float] = field(default_factory=dict)
    status: ResultStatus = ResultStatus.INSUFFICIENT_DATA
    reason: str | None = None
    exact: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecoveryTrendResult:
    tau: float | None
    positions: tuple[int, ...]
    status: ResultStatus
    reason: str | None = None
    excluded: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OrderEffectResult:
    sequence_id: str
    attack_order: tuple[str, ...]
    cumulative_vulnerability: float | None
    status: ResultStatus
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SAEAResult:
    run_id: str
    sequence_id: str
    methodology_version: str
    trajectory: SequentialTrajectory
    per_step: tuple[PerStepVulnerability, ...]
    synergy: SynergyResult
    shapley: ShapleyAttributionResult
    recovery_trend: RecoveryTrendResult
    order_effect: OrderEffectResult
    status: ResultStatus
    reason: str | None
    provenance: Mapping[str, object] = field(default_factory=dict)
