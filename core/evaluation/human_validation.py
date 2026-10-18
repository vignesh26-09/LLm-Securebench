"""Manual validation support without inventing human labels."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class BlindedSample:
    blinded_id: str
    evaluation_id: str
    prompt: str
    response: str
    dimension: str
    provenance: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RaterLabel:
    blinded_id: str
    rater_id: str
    dimension: str
    label: str | None
    adjudication_state: str = "independent"
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.blinded_id or not self.rater_id or not self.dimension:
            raise ValueError("rater labels require blinded_id, rater_id, and dimension")


def export_blinded_samples(rows: Sequence[Mapping[str, object]], *, salt: str, dimension: str) -> tuple[BlindedSample, ...]:
    output = []
    for row in rows:
        evaluation_id = str(row["evaluation_id"])
        blinded = hashlib.sha256(f"{salt}:{evaluation_id}:{dimension}".encode()).hexdigest()[:16]
        output.append(BlindedSample(blinded, evaluation_id, str(row.get("prompt", "")), str(row.get("response", "")), dimension, {"blinding": "sha256-prefix", "source_evaluation_id_retained_for_join": True}))
    return tuple(output)


def agreement_rate(labels: Sequence[RaterLabel]) -> dict[str, object]:
    grouped = _by_item(labels)
    comparable = [items for items in grouped.values() if len(items) >= 2 and all(item.label is not None for item in items)]
    if not comparable:
        return {"agreement_rate": None, "status": "insufficient_data"}
    agree = sum(len({item.label for item in items}) == 1 for items in comparable)
    return {"agreement_rate": agree / len(comparable), "items": len(comparable), "status": "computed"}


def cohens_kappa(labels: Sequence[RaterLabel]) -> dict[str, object]:
    raters = sorted({label.rater_id for label in labels})
    if len(raters) != 2:
        return {"kappa": None, "status": "not_applicable", "reason": "requires_exactly_two_raters"}
    pairs = []
    grouped = _by_item(labels)
    for items in grouped.values():
        by_rater = {item.rater_id: item.label for item in items if item.label is not None}
        if all(rater in by_rater for rater in raters):
            pairs.append((by_rater[raters[0]], by_rater[raters[1]]))
    if not pairs:
        return {"kappa": None, "status": "insufficient_data"}
    labels_set = sorted({value for pair in pairs for value in pair})
    observed = sum(left == right for left, right in pairs) / len(pairs)
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum((left_counts[label] / len(pairs)) * (right_counts[label] / len(pairs)) for label in labels_set)
    return {"kappa": (observed - expected) / (1 - expected) if expected != 1 else None, "observed_agreement": observed, "expected_agreement": expected, "items": len(pairs), "status": "computed" if expected != 1 else "undefined"}


def fleiss_kappa(labels: Sequence[RaterLabel]) -> dict[str, object]:
    raters = sorted({label.rater_id for label in labels})
    if len(raters) < 3:
        return {"kappa": None, "status": "not_applicable", "reason": "requires_three_or_more_raters"}
    grouped = [items for items in _by_item(labels).values() if len({item.rater_id for item in items if item.label is not None}) == len(raters)]
    if not grouped:
        return {"kappa": None, "status": "insufficient_data"}
    categories = sorted({item.label for items in grouped for item in items if item.label is not None})
    n = len(raters)
    p_i = []
    category_totals = Counter()
    for items in grouped:
        counts = Counter(item.label for item in items if item.label is not None)
        category_totals.update(counts)
        p_i.append((sum(count * count for count in counts.values()) - n) / (n * (n - 1)))
    p_bar = sum(p_i) / len(p_i)
    p_e = sum((category_totals[category] / (len(grouped) * n)) ** 2 for category in categories)
    return {"kappa": (p_bar - p_e) / (1 - p_e) if p_e != 1 else None, "items": len(grouped), "raters": n, "status": "computed" if p_e != 1 else "undefined"}


def confusion_matrix(reference: Sequence[RaterLabel], candidate: Sequence[RaterLabel]) -> dict[str, object]:
    reference_by_id = {label.blinded_id: label.label for label in reference if label.label is not None}
    candidate_by_id = {label.blinded_id: label.label for label in candidate if label.label is not None}
    ids = sorted(set(reference_by_id) & set(candidate_by_id))
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item_id in ids:
        counts[str(reference_by_id[item_id])][str(candidate_by_id[item_id])] += 1
    return {"matrix": {row: dict(values) for row, values in counts.items()}, "paired_items": len(ids), "status": "computed" if ids else "insufficient_data"}


def _by_item(labels: Sequence[RaterLabel]) -> dict[str, list[RaterLabel]]:
    grouped: dict[str, list[RaterLabel]] = defaultdict(list)
    for label in labels:
        grouped[label.blinded_id].append(label)
    return grouped
