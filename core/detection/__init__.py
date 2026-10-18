"""Layer 1 fast-detection signals and provider-neutral interfaces."""

from core.detection.aggregation import AggregationConfig, LayerOneAggregator
from core.detection.models import DetectorResult, LayerOneReport, Severity

__all__ = ["AggregationConfig", "DetectorResult", "LayerOneAggregator", "LayerOneReport", "Severity"]
