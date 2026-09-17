"""Versioned judge-to-human comparison artifacts; no judge promotion policy."""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class JudgeCalibrationPair:
    evaluation_id: str
    human_label: bool
    judge_label: bool | None
    attack_family: str | None = None


@dataclass(frozen=True, slots=True)
class JudgeCalibrationArtifact:
    artifact_id: str
    dataset: str
    dataset_revision: str | None
    dataset_hash: str
    sample_size: int
    usable_sample_size: int
    coverage: float
    judge_provider: str
    judge_model: str
    judge_model_version: str | None
    judge_prompt_version: str
    rubric_version: str
    label_mapping: Mapping[str, object]
    human_label_source: str
    agreement: float | None
    cohen_kappa: float | None
    confusion_matrix: Mapping[str, int]
    precision: float | None
    recall: float | None
    f1: float | None
    bootstrap_confidence_intervals: Mapping[str, tuple[float, float] | None]
    strata: Mapping[str, Mapping[str, object]]
    timestamp: str
    software_version: str | None
    provenance: Mapping[str, object] = field(default_factory=dict)
    validation_status: str = "not_validated"


def build_judge_calibration_artifact(
    pairs: Sequence[JudgeCalibrationPair], *, artifact_id: str, dataset: str,
    dataset_revision: str | None, dataset_hash: str, judge_provider: str,
    judge_model: str, judge_model_version: str | None, judge_prompt_version: str,
    rubric_version: str, label_mapping: Mapping[str, object], human_label_source: str,
    software_version: str | None, bootstrap_resamples: int = 2000,
    bootstrap_seed: int = 2026, provenance: Mapping[str, object] | None = None,
) -> JudgeCalibrationArtifact:
    usable = tuple(pair for pair in pairs if pair.judge_label is not None)
    metrics = _metrics(usable)
    intervals = _bootstrap(usable, bootstrap_resamples, bootstrap_seed) if usable else {
        key: None for key in ("agreement", "cohen_kappa", "precision", "recall", "f1")}
    families = sorted({pair.attack_family for pair in usable if pair.attack_family})
    strata = {family: {**_metrics(tuple(pair for pair in usable if pair.attack_family == family)),
                       "n": sum(pair.attack_family == family for pair in usable)} for family in families}
    return JudgeCalibrationArtifact(
        artifact_id, dataset, dataset_revision, dataset_hash, len(pairs), len(usable),
        len(usable) / len(pairs) if pairs else 0.0, judge_provider, judge_model,
        judge_model_version, judge_prompt_version, rubric_version, dict(label_mapping),
        human_label_source, metrics["agreement"], metrics["cohen_kappa"],
        metrics["confusion_matrix"], metrics["precision"], metrics["recall"],
        metrics["f1"], intervals, strata, datetime.now(timezone.utc).isoformat(),
        software_version, dict(provenance or {}), "not_validated",
    )


def _metrics(pairs: Sequence[JudgeCalibrationPair]) -> dict[str, object]:
    if not pairs:
        return {"agreement": None, "cohen_kappa": None,
                "confusion_matrix": {"tn": 0, "fp": 0, "fn": 0, "tp": 0},
                "precision": None, "recall": None, "f1": None}
    tn = sum(not p.human_label and p.judge_label is False for p in pairs)
    fp = sum(not p.human_label and p.judge_label is True for p in pairs)
    fn = sum(p.human_label and p.judge_label is False for p in pairs)
    tp = sum(p.human_label and p.judge_label is True for p in pairs)
    n = len(pairs)
    agreement = (tn + tp) / n
    human_positive = (fn + tp) / n
    judge_positive = (fp + tp) / n
    expected = human_positive * judge_positive + (1 - human_positive) * (1 - judge_positive)
    kappa = (agreement - expected) / (1 - expected) if expected < 1 else None
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {"agreement": agreement, "cohen_kappa": kappa,
            "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "precision": precision, "recall": recall, "f1": f1}


def _bootstrap(pairs: Sequence[JudgeCalibrationPair], resamples: int, seed: int):
    if resamples <= 0:
        raise ValueError("bootstrap_resamples must be positive")
    rng = random.Random(seed)
    values = {key: [] for key in ("agreement", "cohen_kappa", "precision", "recall", "f1")}
    for _ in range(resamples):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        result = _metrics(sample)
        for key in values:
            value = result[key]
            if isinstance(value, (int, float)) and math.isfinite(value):
                values[key].append(float(value))
    return {key: _percentile_ci(items) for key, items in values.items()}


def _percentile_ci(values: list[float]) -> tuple[float, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(0.025 * (len(ordered) - 1))], ordered[int(0.975 * (len(ordered) - 1))]
