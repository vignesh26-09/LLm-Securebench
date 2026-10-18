"""Layer 1 fast-detection ports; implementations emit signals rather than verdicts."""

from typing import Protocol

from core.detection.models import DetectorResult


class LayerOneDetector(Protocol):
    """A fast, provider-independent source of one or more heuristic signals."""
    @property
    def name(self) -> str: ...

    def detect(self, text: str) -> DetectorResult: ...


class SemanticSimilarityDetector(LayerOneDetector, Protocol):
    """Reserved interface for a future semantic Layer 1 adapter; no implementation exists."""


class ToxicityDetector(LayerOneDetector, Protocol):
    """Reserved interface for a future toxicity Layer 1 adapter; no implementation exists."""
