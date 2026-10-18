"""Versioned exact-disclosure outcomes; no raw response or secret fields."""

from dataclasses import dataclass, field
from typing import Literal


CHECKER_VERSION = "exact-contiguous-v1"
DIAGNOSTIC_VERSION = "nonprimary-candidates-v1"


@dataclass(frozen=True, slots=True)
class DefenderResponse:
    response_id: str
    text: str | None = field(repr=False)
    defender_generated: bool = True
    valid: bool = True
    finish_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SecondarySignals:
    """Candidate patterns only; never substitute for the exact primary event."""

    canonicalized_candidate: bool = False
    partial_candidate: bool = False
    encoded_candidate: bool = False
    obfuscated_candidate: bool = False
    wrong_trial_exact_candidate: bool = False
    version: str = DIAGNOSTIC_VERSION
    scope: str = "diagnostic_only_not_validated_semantic_leakage"


@dataclass(frozen=True, slots=True)
class DisclosureOutcome:
    status: Literal["computed", "incomplete_trajectory", "missing_final", "invalid_response"]
    reason: str | None
    y_final: int | None
    y_earlier: int | None
    y_ever: int | None
    final_response_sha256: str | None
    earlier_response_sha256: tuple[str, ...]
    earlier_exact_observed_in_partial_trajectory: bool
    secondary: SecondarySignals
    checker_version: str = CHECKER_VERSION
