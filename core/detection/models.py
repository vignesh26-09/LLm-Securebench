"""Framework-independent schemas for Layer 1 fast-detection signals."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class Severity(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class DetectorResult:
    """One heuristic detector signal, not a ground-truth verdict."""
    detector_name: str
    score: float
    matched_evidence: tuple[str, ...] = ()
    confidence: float | None = None
    signal_scores: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_unit_interval("score", self.score)
        if self.confidence is not None:
            _validate_unit_interval("confidence", self.confidence)
        for name, value in self.signal_scores.items():
            _validate_unit_interval(f"signal_scores[{name!r}]", value)


@dataclass(frozen=True, slots=True)
class SeverityThresholds:
    """Configurable boundaries for translating aggregate score to a severity label."""
    low: float = 0.25
    medium: float = 0.5
    high: float = 0.75
    critical: float = 0.9

    def __post_init__(self) -> None:
        values = (self.low, self.medium, self.high, self.critical)
        if any(not 0.0 <= value <= 1.0 for value in values) or values != tuple(sorted(values)):
            raise ValueError("severity thresholds must be ordered values between 0 and 1")

    def classify(self, score: float) -> Severity:
        _validate_unit_interval("score", score)
        if score >= self.critical:
            return Severity.CRITICAL
        if score >= self.high:
            return Severity.HIGH
        if score >= self.medium:
            return Severity.MEDIUM
        if score >= self.low:
            return Severity.LOW
        return Severity.NONE


@dataclass(frozen=True, slots=True)
class LayerOneReport:
    """Combined Layer 1 signals. It is not a security judgment or ground truth."""
    detector_results: tuple[DetectorResult, ...]
    injection_score: float
    leakage_score: float
    jailbreak_score: float
    aggregate_score: float
    severity: Severity
    attack_success_signal: bool | None
    metadata: Mapping[str, object] = field(default_factory=dict)


def _validate_unit_interval(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
