"""Statistical-analysis ports and deterministic session-bootstrap support."""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean
from typing import Protocol, Sequence

from core.saea.models import ResultStatus, SAEAResult


@dataclass(frozen=True, slots=True)
class SessionBootstrapResult:
    estimate: float | None
    confidence_interval: tuple[float, float] | None
    sample_size: int
    status: ResultStatus
    reason: str | None = None
    resamples: int = 1000
    confidence: float = 0.95
    seed: int = 0


class OrderEffectAnalyzer(Protocol):
    """Port for Friedman/mixed-effects analysis supplied by a statistics adapter."""
    def analyze(self, results: Sequence[SAEAResult]) -> object: ...


class GrowthCurveAnalyzer(Protocol):
    """Port for the approved linear/MM/exponential/power-law model comparison."""
    def analyze(self, results: Sequence[SAEAResult]) -> object: ...


def bootstrap_synergy(results: Sequence[SAEAResult], *, resamples: int = 1000, confidence: float = 0.95, seed: int = 0) -> SessionBootstrapResult:
    """Bootstrap independent defined-session SI values; undefined sessions are excluded."""
    if resamples <= 0 or not 0.0 < confidence < 1.0:
        raise ValueError("invalid bootstrap configuration")
    values = [result.synergy.synergy_index for result in results if result.synergy.status is ResultStatus.APPLICABLE and result.synergy.synergy_index is not None]
    if len(values) < 2:
        return SessionBootstrapResult(mean(values) if values else None, None, len(values), ResultStatus.INSUFFICIENT_DATA, "insufficient_defined_sessions", resamples, confidence, seed)
    generator = random.Random(seed)
    samples = sorted(mean(generator.choice(values) for _ in values) for _ in range(resamples))
    alpha = (1.0 - confidence) / 2.0
    lower = samples[min(resamples - 1, int(alpha * resamples))]
    upper = samples[min(resamples - 1, int((1.0 - alpha) * resamples))]
    return SessionBootstrapResult(mean(values), (lower, upper), len(values), ResultStatus.APPLICABLE, resamples=resamples, confidence=confidence, seed=seed)
