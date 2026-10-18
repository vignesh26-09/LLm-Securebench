"""Configurable aggregation for Layer 1 detector signals, not ground-truth scoring."""

from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence

from core.detection.models import DetectorResult, LayerOneReport, SeverityThresholds

_SIGNALS = ("injection", "leakage", "jailbreak")


class AttackSuccessRule(Protocol):
    """Explicit project policy for deriving an attack-success signal, if one is desired."""
    def evaluate(self, signal_scores: Mapping[str, float], detector_results: Sequence[DetectorResult]) -> bool | None: ...


@dataclass(frozen=True, slots=True)
class ThresholdAttackSuccessRule:
    """A configurable policy; it is not a universal definition of attack success."""
    minimum_scores: Mapping[str, float]
    min_matches: int = 1

    def __post_init__(self) -> None:
        if not self.minimum_scores:
            raise ValueError("minimum_scores must not be empty")
        if self.min_matches <= 0:
            raise ValueError("min_matches must be positive")
        if any(not 0.0 <= value <= 1.0 for value in self.minimum_scores.values()):
            raise ValueError("attack-success thresholds must be between 0 and 1")

    def evaluate(self, signal_scores: Mapping[str, float], detector_results: Sequence[DetectorResult]) -> bool:
        matches = sum(signal_scores.get(name, 0.0) >= threshold for name, threshold in self.minimum_scores.items())
        return matches >= self.min_matches


@dataclass(frozen=True, slots=True)
class AggregationConfig:
    signal_weights: Mapping[str, float] = field(default_factory=lambda: {"injection": 1.0, "leakage": 1.0, "jailbreak": 1.0})
    severity_thresholds: SeverityThresholds = field(default_factory=SeverityThresholds)
    attack_success_rule: AttackSuccessRule | None = None

    def __post_init__(self) -> None:
        if not self.signal_weights or any(weight < 0 for weight in self.signal_weights.values()):
            raise ValueError("signal weights must be non-empty and non-negative")
        if not any(self.signal_weights.values()):
            raise ValueError("at least one signal weight must be positive")


class LayerOneAggregator:
    """Combines detector evidence using maximum per-signal scores and configured weights."""
    def __init__(self, config: AggregationConfig = AggregationConfig()) -> None:
        self._config = config

    def aggregate(self, detector_results: Sequence[DetectorResult]) -> LayerOneReport:
        signals = {name: max((result.signal_scores.get(name, 0.0) for result in detector_results), default=0.0) for name in _SIGNALS}
        weights = self._config.signal_weights
        aggregate_score = sum(signals.get(name, 0.0) * weight for name, weight in weights.items()) / sum(weights.values())
        attack_success = self._config.attack_success_rule.evaluate(signals, detector_results) if self._config.attack_success_rule else None
        return LayerOneReport(
            tuple(detector_results), signals["injection"], signals["leakage"], signals["jailbreak"],
            aggregate_score, self._config.severity_thresholds.classify(aggregate_score), attack_success,
            {"aggregation": "maximum per signal, weighted mean", "signal_weights": dict(weights)},
        )
