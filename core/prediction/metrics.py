"""Binary-fixture metric calculations with explicit undefined states."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class MetricValue:
    value: float | None
    status: str
    reason: str | None = None


def evaluate_binary(labels: Sequence[int], scores: Sequence[float], *, threshold: float | None = None) -> dict[str, MetricValue]:
    if len(labels) != len(scores) or not labels or any(label not in (0, 1) for label in labels) or any(not 0 <= score <= 1 for score in scores):
        raise ValueError("metrics require aligned non-empty binary labels and unit scores")
    result = {"prevalence": MetricValue(sum(labels) / len(labels), "computed")}
    if len(set(labels)) < 2:
        for name in ("roc_auc", "average_precision", "brier", "log_loss"):
            result[name] = MetricValue(None, "undefined", "one_class_evaluation_labels")
    else:
        result.update({"roc_auc": MetricValue(_roc_auc(labels, scores), "computed"), "average_precision": MetricValue(_average_precision(labels, scores), "computed"), "brier": MetricValue(sum((score - label) ** 2 for label, score in zip(labels, scores, strict=True)) / len(labels), "computed"), "log_loss": MetricValue(-sum(label * math.log(_clip(score)) + (1 - label) * math.log(_clip(1 - score)) for label, score in zip(labels, scores, strict=True)) / len(labels), "computed")})
    for name in ("precision", "recall", "f1", "balanced_accuracy", "mcc"):
        result[name] = MetricValue(None, "not_computed", "threshold_not_supplied")
    if threshold is not None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be in [0, 1]")
        result.update(_threshold_metrics(labels, scores, threshold))
    return result


def _roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    positive = [score for label, score in zip(labels, scores, strict=True) if label == 1]
    negative = [score for label, score in zip(labels, scores, strict=True) if label == 0]
    return sum(1.0 if left > right else 0.5 if left == right else 0.0 for left in positive for right in negative) / (len(positive) * len(negative))


def _average_precision(labels: Sequence[int], scores: Sequence[float]) -> float:
    ordered = sorted(zip(scores, labels, strict=True), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    found = 0
    total = 0.0
    for rank, (_, label) in enumerate(ordered, 1):
        if label:
            found += 1
            total += found / rank
    return total / positives


def _threshold_metrics(labels: Sequence[int], scores: Sequence[float], threshold: float) -> dict[str, MetricValue]:
    predicted = [int(score >= threshold) for score in scores]
    tp = sum(actual == 1 and guess == 1 for actual, guess in zip(labels, predicted, strict=True))
    tn = sum(actual == 0 and guess == 0 for actual, guess in zip(labels, predicted, strict=True))
    fp = sum(actual == 0 and guess == 1 for actual, guess in zip(labels, predicted, strict=True))
    fn = sum(actual == 1 and guess == 0 for actual, guess in zip(labels, predicted, strict=True))
    precision = _division(tp, tp + fp)
    recall = _division(tp, tp + fn)
    f1 = _division(2 * precision * recall, precision + recall) if precision is not None and recall is not None else None
    specificity = _division(tn, tn + fp)
    balanced = (recall + specificity) / 2 if recall is not None and specificity is not None else None
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denominator if denominator else None
    return {"precision": _metric(precision), "recall": _metric(recall), "f1": _metric(f1), "balanced_accuracy": _metric(balanced), "mcc": _metric(mcc)}


def _metric(value: float | None) -> MetricValue:
    return MetricValue(value, "computed" if value is not None else "undefined", None if value is not None else "zero_denominator")


def _division(left: float, right: float) -> float | None:
    return left / right if right else None


def _clip(value: float) -> float:
    return min(1 - 1e-15, max(1e-15, value))
