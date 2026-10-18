"""Descriptive Mode B diagnostics; no aggregation, weighting, or feature removal."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence

from core.draa.models import DRAAEvidenceRecord, DRAAStatus


@dataclass(frozen=True, slots=True)
class EvidenceDiagnostics:
    record_count: int
    feature_count: int
    availability_by_source: Mapping[str, int]
    status_counts: Mapping[str, int]
    uncertainty_available_count: int
    warnings: tuple[str, ...] = ()


def summarize(records: Sequence[DRAAEvidenceRecord]) -> EvidenceDiagnostics:
    sources: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    uncertainty = 0
    features = 0
    for record in records:
        for feature in record.features:
            features += 1
            statuses[feature.status.value] += 1
            if feature.status is DRAAStatus.APPLICABLE:
                sources[feature.namespace] += 1
            if feature.uncertainty is not None:
                uncertainty += 1
    return EvidenceDiagnostics(len(records), features, dict(sources), dict(statuses), uncertainty)


def correlation_ready_series(records: Sequence[DRAAEvidenceRecord]) -> Mapping[str, tuple[float | None, ...]]:
    """Exports only explicitly numeric, same-name feature values; does not correlate them."""
    names = sorted({f"{feature.namespace}.{feature.name}" for record in records for feature in record.features})
    output: dict[str, tuple[float | None, ...]] = {}
    for name in names:
        values: list[float | None] = []
        namespace, feature_name = name.split(".", 1)
        for record in records:
            match = next((feature for feature in record.features if feature.namespace == namespace and feature.name == feature_name), None)
            if match is not None and match.status is DRAAStatus.APPLICABLE and isinstance(match.raw_value, (int, float)) and not isinstance(match.raw_value, bool):
                values.append(float(match.raw_value))
            else:
                values.append(None)
        output[name] = tuple(values)
    return output
