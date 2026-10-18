"""Minimal paired analyses for pre-matched experimental observations."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from statistics import fmean
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class PairedValue:
    pair_id: str
    left: float | None
    right: float | None
    groups: Mapping[str, str] = field(default_factory=dict)
    exclusion_reason: str | None = None


@dataclass(frozen=True, slots=True)
class AnalysisRecord:
    analysis_version: str
    sample_definition: str
    inclusion_rules: tuple[str, ...]
    exclusion_rules: tuple[str, ...]
    n: int
    missingness: Mapping[str, int]
    statistic: Mapping[str, float | None]
    effect_size: Mapping[str, float | None]
    confidence_interval: tuple[float, float] | None
    seed: int
    grouping_variables: Mapping[str, str]
    provenance: Mapping[str, object]
    status: str
    reason: str | None = None


def paired_difference_analysis(values: Sequence[PairedValue], *, sample_definition: str,
                               seed: int = 2026, resamples: int = 2000,
                               grouping_variables: Mapping[str, str] | None = None,
                               provenance: Mapping[str, object] | None = None) -> AnalysisRecord:
    included = [value for value in values if value.left is not None and value.right is not None]
    missing = {"left_missing": sum(value.left is None for value in values),
               "right_missing": sum(value.right is None for value in values),
               "explicitly_excluded": sum(value.exclusion_reason is not None for value in values)}
    if not included:
        return AnalysisRecord("paired-analysis-v1", sample_definition,
            ("both paired values available",), ("missing or explicitly excluded pair",),
            0, missing, {"mean_left": None, "mean_right": None, "mean_difference": None},
            {"paired_standardized_mean_difference": None}, None, seed,
            dict(grouping_variables or {}), dict(provenance or {}), "unsupported",
            "no_complete_pairs")
    differences = [float(value.right) - float(value.left) for value in included]
    mean_difference = fmean(differences)
    if len(differences) < 2:
        effect = None
        ci = None
        status = "insufficient_data"
        reason = "at_least_two_pairs_required_for_uncertainty"
    else:
        sd = math.sqrt(sum((item - mean_difference) ** 2 for item in differences) / (len(differences) - 1))
        effect = mean_difference / sd if sd > 0 else None
        rng = random.Random(seed)
        boot = sorted(fmean(differences[rng.randrange(len(differences))] for _ in differences) for _ in range(resamples))
        ci = (boot[int(.025 * (len(boot) - 1))], boot[int(.975 * (len(boot) - 1))])
        status = "computed"
        reason = None
    return AnalysisRecord("paired-analysis-v1", sample_definition,
        ("pre-matched pair identity", "both values available"),
        ("missing value", "failed evaluation", "identity mismatch"), len(included), missing,
        {"mean_left": fmean(float(item.left) for item in included),
         "mean_right": fmean(float(item.right) for item in included),
         "mean_difference": mean_difference},
        {"paired_standardized_mean_difference": effect}, ci, seed,
        dict(grouping_variables or {}), dict(provenance or {}), status, reason)


def grouped_paired_analyses(values: Sequence[PairedValue], *, group: str, sample_definition: str,
                            seed: int = 2026, resamples: int = 2000) -> Mapping[str, AnalysisRecord]:
    keys = sorted({item.groups[group] for item in values if group in item.groups})
    return {key: paired_difference_analysis(
        [item for item in values if item.groups.get(group) == key],
        sample_definition=sample_definition, seed=seed, resamples=resamples,
        grouping_variables={group: key}) for key in keys}
