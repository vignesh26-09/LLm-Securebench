"""Typed Recovery Capability contracts from the approved RC specification."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

RC_METHODOLOGY_VERSION = "rc-reconciled-v1"
RC_DISTANCE_ID = "normalized_euclidean_v1"
REQUIRED_DIMENSIONS = frozenset({"safety", "helpfulness"})


class RCResultStatus(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNCALIBRATED = "uncalibrated"
    INCOMPATIBLE = "calibration_artifact_incompatible"
    UNDEFINED = "undefined"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED_EVALUATION = "failed_evaluation"


class RCContextStatus(StrEnum):
    RETAINED = "retained"
    TRUNCATED = "truncated"
    UNKNOWN = "unknown"
    RESET = "reset"


@dataclass(frozen=True, slots=True)
class BehavioralState:
    state_id: str
    scores: Mapping[str, float]
    status: RCResultStatus = RCResultStatus.APPLICABLE
    reason: str | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.state_id:
            raise ValueError("behavioral state requires state_id")
        for dimension, value in self.scores.items():
            if not dimension or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("behavioral state scores must be finite values in [0, 1]")


@dataclass(frozen=True, slots=True)
class RecoveryStep:
    turn_index: int
    state: BehavioralState

    def __post_init__(self) -> None:
        if self.turn_index <= 0:
            raise ValueError("recovery step turn_index must be positive")


@dataclass(frozen=True, slots=True)
class RCCalibrationArtifact:
    artifact_id: str
    methodology_version: str
    distance_id: str
    dimension_schema: tuple[str, ...]
    delta_a_min: float
    latency_epsilon: float | None = None
    relapse_delta: float | None = None
    validation_status: str = "unvalidated"
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id or not self.methodology_version or not self.distance_id:
            raise ValueError("calibration artifact requires identity and versions")
        if not REQUIRED_DIMENSIONS <= set(self.dimension_schema):
            raise ValueError("calibration artifact must include safety and helpfulness")
        if isinstance(self.delta_a_min, bool) or not isinstance(self.delta_a_min, (int, float)) or not math.isfinite(self.delta_a_min) or self.delta_a_min <= 0:
            raise ValueError("delta_a_min must be positive and finite")
        for name, value in (("latency_epsilon", self.latency_epsilon), ("relapse_delta", self.relapse_delta)):
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be non-negative and finite")


@dataclass(frozen=True, slots=True)
class RecoveryRunInput:
    run_id: str
    model_id: str
    session_id: str | None
    baseline_states: tuple[BehavioralState, ...]
    attack_state: BehavioralState
    recovery_steps: tuple[RecoveryStep, ...]
    dimension_schema: tuple[str, ...] = ("safety", "helpfulness")
    methodology_version: str = RC_METHODOLOGY_VERSION
    context_status: RCContextStatus = RCContextStatus.UNKNOWN
    generation_config: Mapping[str, object] = field(default_factory=dict)
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id or not self.model_id:
            raise ValueError("recovery run requires run_id and model_id")
        if not REQUIRED_DIMENSIONS <= set(self.dimension_schema):
            raise ValueError("recovery run dimension schema must include safety and helpfulness")
        if not self.baseline_states:
            raise ValueError("baseline_states must be non-empty")
        if not self.recovery_steps:
            raise ValueError("recovery_steps must be non-empty")
        if tuple(step.turn_index for step in self.recovery_steps) != tuple(range(1, len(self.recovery_steps) + 1)):
            raise ValueError("recovery step indices must be contiguous from 1")


@dataclass(frozen=True, slots=True)
class RecoveryRunResult:
    run_id: str
    model_id: str
    session_id: str | None
    methodology_version: str
    distance_id: str
    active_dimensions: tuple[str, ...]
    excluded_dimensions: Mapping[str, str]
    baseline_mean: Mapping[str, float] | None
    attack_vector: Mapping[str, float] | None
    delta_a: float | None
    recovery_deltas: tuple[tuple[int, float], ...]
    rc_auc_raw: float | None
    terminal_recovery_raw: float | None
    rc_auc_bounded: float | None
    terminal_recovery_bounded: float | None
    status: RCResultStatus
    reason: str | None
    calibration_artifact: Mapping[str, object] | None
    context_status: RCContextStatus
    diagnostics: Mapping[str, object] = field(default_factory=dict)
    provenance: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecoveryCapabilityResult:
    runs: tuple[RecoveryRunResult, ...]
    expected_run_count: int
    status_counts: Mapping[str, int]
    mean_rc_auc_raw: float | None
    mean_terminal_recovery_raw: float | None
    mean_rc_auc_bounded: float | None
    mean_terminal_recovery_bounded: float | None
    sample_variance_rc_auc_raw: float | None
    sample_variance_terminal_recovery_raw: float | None
    provenance: Mapping[str, object] = field(default_factory=dict)
