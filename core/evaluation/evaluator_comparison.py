"""Fair, source-aligned binary evaluator diagnostics; never promotes a judge."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Mapping, Sequence


def compare_binary_evaluators(rows: Sequence[Mapping[str, object]], *,
                              evaluator_names: Sequence[str],
                              bootstrap_resamples: int = 1000,
                              bootstrap_seed: int = 2026,
                              require_held_out: bool = False) -> dict[str, object]:
    """Compare pre-existing binary predictions on identical usable record IDs.

    `group_id` denotes related prompts. If absent, intervals are unavailable;
    independent-row bootstrap is deliberately not substituted.
    """
    if not rows or not evaluator_names or len(set(evaluator_names)) != len(evaluator_names):
        raise ValueError("rows and unique evaluator names are required")
    if bootstrap_resamples <= 0:
        raise ValueError("bootstrap_resamples must be positive")
    ids: set[str] = set()
    for row in rows:
        record_id = row.get("evaluation_id")
        if not isinstance(record_id, str) or not record_id or record_id in ids:
            raise ValueError("evaluation IDs must be nonempty and unique")
        ids.add(record_id)
        if type(row.get("human_label")) is not bool:
            raise ValueError("reference human label must be binary")
        predictions = row.get("predictions")
        if not isinstance(predictions, Mapping):
            raise ValueError("predictions mapping required")
        for name in evaluator_names:
            if name not in predictions or predictions[name] is not None and type(predictions[name]) is not bool:
                raise ValueError(f"missing or non-binary prediction for {name}")
    if require_held_out and any(row.get("split") != "test" for row in rows):
        raise ValueError("held-out comparison requires every row in the frozen test split")
    common = [row for row in rows if all(row["predictions"][name] is not None for name in evaluator_names)]
    if not common:
        return {"status": "insufficient_data", "reason": "no_common_usable_records",
                "source_n": len(rows), "common_n": 0}
    grouped = all(isinstance(row.get("group_id"), str) and row["group_id"] for row in common)
    by_name = {}
    for name in evaluator_names:
        own_usable = [row for row in rows if row["predictions"][name] is not None]
        common_stats = _binary_stats(common, name)
        common_stats["cluster_bootstrap_intervals"] = (
            _cluster_intervals(common, name, bootstrap_resamples, bootstrap_seed) if grouped else None)
        strata: dict[str, object] = {}
        for family in sorted({row.get("attack_family") for row in common if isinstance(row.get("attack_family"), str)}):
            subset = [row for row in common if row.get("attack_family") == family]
            strata[family] = _binary_stats(subset, name)
        by_name[name] = {"source_coverage_n": len(own_usable),
                         "source_coverage": len(own_usable) / len(rows),
                         "common_case": common_stats,
                         "attack_family_strata": strata if strata else None}
    return {"status": "held_out_test" if require_held_out else "exploratory_no_declared_test_split",
            "source_n": len(rows), "common_n": len(common),
            "common_case_coverage": len(common) / len(rows),
            "interval_unit": "related_group_cluster" if grouped else "unavailable_missing_group_id",
            "evaluators": by_name}


def _binary_stats(rows, name):
    n = len(rows)
    tp = sum(row["human_label"] and row["predictions"][name] for row in rows)
    fn = sum(row["human_label"] and not row["predictions"][name] for row in rows)
    fp = sum(not row["human_label"] and row["predictions"][name] for row in rows)
    tn = n - tp - fn - fp
    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    balanced = (recall + specificity) / 2 if recall is not None and specificity is not None else None
    human_positive = (tp + fn) / n
    predicted_positive = (tp + fp) / n
    expected = human_positive * predicted_positive + (1 - human_positive) * (1 - predicted_positive)
    kappa = (accuracy - expected) / (1 - expected) if expected < 1 else None
    return {"n": n, "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "accuracy": accuracy, "raw_agreement": accuracy, "precision": precision,
            "recall": recall, "specificity": specificity, "f1": f1,
            "balanced_accuracy": balanced, "cohen_kappa": kappa,
            "false_positive_rate": fp / (fp + tn) if fp + tn else None,
            "false_negative_rate": fn / (fn + tp) if fn + tp else None}


def _cluster_intervals(rows, name, resamples, seed):
    groups = defaultdict(list)
    for row in rows:
        groups[row["group_id"]].append(row)
    keys = sorted(groups)
    rng = random.Random(seed)
    fields = ("accuracy", "precision", "recall", "specificity", "f1",
              "balanced_accuracy", "cohen_kappa", "false_positive_rate", "false_negative_rate")
    values: dict[str, list[float]] = {field: [] for field in fields}
    for _ in range(resamples):
        sample = [row for _ in keys for row in groups[keys[rng.randrange(len(keys))]]]
        stats = _binary_stats(sample, name)
        for field in fields:
            value = stats[field]
            if isinstance(value, (int, float)) and math.isfinite(value):
                values[field].append(float(value))
    return {field: _percentile_interval(values[field]) for field in fields}


def _percentile_interval(values):
    if not values:
        return None
    ordered = sorted(values)
    return [ordered[int(.025 * (len(ordered) - 1))], ordered[int(.975 * (len(ordered) - 1))]]
