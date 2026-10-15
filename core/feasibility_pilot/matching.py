"""Preassigned structural matching and separate post-response diagnostics."""

from dataclasses import dataclass
import re

from core.feasibility_pilot.cases import digest


@dataclass(frozen=True, slots=True)
class NumericTolerance:
    model_id: str
    max_token_difference: int
    max_relative_token_difference: float
    max_occupancy_difference: float
    development_evidence_sha256: str
    approved_by: str | None = None

    def __post_init__(self) -> None:
        if (not self.model_id or not self.development_evidence_sha256
                or self.max_token_difference < 0
                or not 0 <= self.max_relative_token_difference <= 1
                or not 0 <= self.max_occupancy_difference <= 1):
            raise ValueError("Invalid development-derived tolerance")

    @property
    def content_sha256(self) -> str:
        from dataclasses import asdict
        return digest(asdict(self))

    def require_real_execution_approval(self) -> None:
        if not self.approved_by:
            raise ValueError("Numeric matching tolerance lacks approval")


@dataclass(frozen=True, slots=True)
class PlannedHistory:
    model_id: str
    goal_id: str
    task_id: str
    probe_family_id: str
    topic_review_id: str
    user_turn_count: int
    role_sequence: tuple[str, ...]
    exposure_position: int
    probe_position: int
    generation_sha256: str
    script_version: str
    planned_tokens: int
    planned_occupancy: float


@dataclass(frozen=True, slots=True)
class PlannedMatch:
    matched: bool
    reasons: tuple[str, ...]
    tolerance_sha256: str


def compare_planned(left: PlannedHistory, right: PlannedHistory,
                    tolerance: NumericTolerance) -> PlannedMatch:
    reasons = []
    for key in ("model_id", "goal_id", "task_id", "probe_family_id",
                "topic_review_id", "user_turn_count", "role_sequence",
                "exposure_position", "probe_position", "generation_sha256",
                "script_version"):
        if getattr(left, key) != getattr(right, key):
            reasons.append(f"{key}_mismatch")
    if left.model_id != tolerance.model_id or right.model_id != tolerance.model_id:
        reasons.append("tolerance_model_mismatch")
    if abs(left.planned_tokens - right.planned_tokens) > tolerance.max_token_difference:
        reasons.append("token_absolute_mismatch")
    denominator = max(left.planned_tokens, right.planned_tokens, 1)
    if abs(left.planned_tokens - right.planned_tokens) / denominator > tolerance.max_relative_token_difference:
        reasons.append("token_relative_mismatch")
    if abs(left.planned_occupancy - right.planned_occupancy) > tolerance.max_occupancy_difference:
        reasons.append("occupancy_mismatch")
    return PlannedMatch(not reasons, tuple(reasons), tolerance.content_sha256)


@dataclass(frozen=True, slots=True)
class RealizedHistory:
    trial_id: str
    provider_input_tokens: int | None
    defender_output_tokens: int | None
    realized_refusals: int
    realized_occupancy: float | None
    completed: bool
    # Descriptive post-treatment data; never an allocation or pairing input.


@dataclass(frozen=True, slots=True)
class TokenDistanceTolerance:
    """Secondary d=2 versus d=5 comparison, learned only on development data."""

    model_id: str
    max_planned_token_difference: int
    development_evidence_sha256: str
    approved_by: str | None = None
    version: str = "token-distance-control-v1"

    def __post_init__(self) -> None:
        if (not self.model_id or self.max_planned_token_difference < 0
                or not re.fullmatch(r"[0-9a-f]{64}", self.development_evidence_sha256)
                or self.version != "token-distance-control-v1"):
            raise ValueError("Invalid token-distance control tolerance")

    @property
    def content_sha256(self) -> str:
        from dataclasses import asdict
        return digest(asdict(self))

    def require_real_execution_approval(self) -> None:
        if not self.approved_by:
            raise ValueError("Token-distance control tolerance is not approved")


@dataclass(frozen=True, slots=True)
class TokenDistanceComparison:
    d2_trial_id: str
    d5_trial_id: str
    tolerance_sha256: str
    status: str
    planned_difference: int | None
    within_planned_tolerance: bool | None
    observed_proxy_difference: int | None
    reason: str | None


def compare_token_distance_control(d2_assignment: object, d5_assignment: object,
                                   d2_schedule: object, d5_schedule: object,
                                   tolerance: TokenDistanceTolerance,
                                   *, observed_proxy_d2: int | None = None,
                                   observed_proxy_d5: int | None = None) -> TokenDistanceComparison:
    """A descriptive secondary control; never reassigns or filters A/T pairs."""
    fields = ("protocol_sha256", "model_id", "goal_id", "repetition", "arm",
              "probe_variant_id", "probe_version", "script_version")
    if (getattr(d2_assignment, "distance") != 2 or getattr(d5_assignment, "distance") != 5
            or getattr(d2_assignment, "arm").value not in {"A", "T"}
            or any(getattr(d2_assignment, field) != getattr(d5_assignment, field)
                   for field in fields)
            or d2_assignment.model_id != tolerance.model_id
            or d2_schedule.trial_id != d2_assignment.trial_id
            or d5_schedule.trial_id != d5_assignment.trial_id
            or d2_schedule.token_control_group_id is None
            or d2_schedule.token_control_group_id != d5_schedule.token_control_group_id):
        raise ValueError("Secondary token-control cells are not preassigned counterparts")
    observed = (abs(observed_proxy_d2 - observed_proxy_d5)
                if observed_proxy_d2 is not None and observed_proxy_d5 is not None else None)
    if d2_schedule.planned_token_distance is None or d5_schedule.planned_token_distance is None:
        return TokenDistanceComparison(d2_assignment.trial_id, d5_assignment.trial_id,
                                       tolerance.content_sha256,
                                       "unavailable", None, None, observed,
                                       "planned_token_distance_unavailable")
    difference = abs(d2_schedule.planned_token_distance - d5_schedule.planned_token_distance)
    matched = difference <= tolerance.max_planned_token_difference
    return TokenDistanceComparison(d2_assignment.trial_id, d5_assignment.trial_id,
                                   tolerance.content_sha256,
                                   "planned_matched" if matched else "planned_mismatch",
                                   difference, matched, observed,
                                   None if matched else "development_tolerance_exceeded")
