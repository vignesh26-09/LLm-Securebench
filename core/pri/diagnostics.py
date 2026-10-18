"""Mode B descriptive profile diagnostics; never robustness estimation."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, variance
from typing import Mapping

from core.pri.models import PRIProfileRecord


@dataclass(frozen=True, slots=True)
class PRIProfileDiagnostics:
    requested_categories: int
    observed_categories: int
    source_counts: Mapping[str, int]
    status_counts: Mapping[str, int]
    hierarchy_counts: Mapping[str, int]
    uncertainty_available: int
    numeric_descriptions: Mapping[str, Mapping[str, float | int]]


def summarize(profile: PRIProfileRecord) -> PRIProfileDiagnostics:
    sources: dict[str, int] = {}
    statuses: dict[str, int] = {}
    numeric: dict[str, list[float]] = {}
    uncertainty = 0
    for cell in profile.cells:
        sources[cell.source_namespace] = sources.get(cell.source_namespace, 0) + 1
        statuses[cell.status.value] = statuses.get(cell.status.value, 0) + 1
        if cell.uncertainty is not None:
            uncertainty += 1
        if cell.status.value == "applicable" and isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
            numeric.setdefault(f"{cell.source_namespace}.{cell.source_feature_name}", []).append(float(cell.value))
    descriptions = {name: _describe(values) for name, values in numeric.items()}
    coverage = profile.coverage
    return PRIProfileDiagnostics(len(profile.population.requested_categories), len(profile.population.observed_categories), sources, statuses, dict(coverage.hierarchy_counts if coverage else {}), uncertainty, descriptions)


def _describe(values: list[float]) -> Mapping[str, float | int]:
    ordered = sorted(values)
    output: dict[str, float | int] = {"count": len(values), "min": ordered[0], "max": ordered[-1], "mean": mean(values), "median": median(values)}
    if len(values) > 1:
        output["variance"] = variance(values)
    return output
