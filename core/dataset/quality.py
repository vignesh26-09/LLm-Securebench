"""Configurable, exploratory Dataset Quality Index (DQI) components.

DQI is a research aid, not a scientifically validated quality measure.
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from core.dataset.duplicates import find_dataset_duplicates
from core.dataset.models import Dataset
from core.dataset.semantic import Embedding, cosine_similarity


def normalized_entropy(values: Sequence[str | None]) -> float:
    """Return categorical Shannon entropy normalized to [0, 1]."""
    counts = Counter(value for value in values if value is not None)
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    return entropy / math.log2(len(counts))


@dataclass(frozen=True, slots=True)
class CoverageStatistics:
    record_count: int
    prompt_coverage: float
    field_coverage: dict[str, float]


def calculate_coverage_statistics(dataset: Dataset) -> CoverageStatistics:
    """Measure presence rates for optional schema fields, not semantic completeness."""
    fields = ("id", "prompt", "category", "attack_type", "source", "language", "difficulty")
    total = len(dataset.records)
    coverage = {field: (sum(getattr(record, field) is not None for record in dataset.records) / total if total else 0.0) for field in fields}
    return CoverageStatistics(total, coverage["prompt"], coverage)


def difficulty_distribution(dataset: Dataset) -> dict[str, int]:
    return dict(Counter(record.difficulty for record in dataset.records if record.difficulty is not None))


@dataclass(frozen=True, slots=True)
class CategoryBalance:
    counts: dict[str, int]
    normalized_entropy: float


def analyze_category_balance(dataset: Dataset) -> CategoryBalance:
    values = [record.category for record in dataset.records]
    return CategoryBalance(dict(Counter(value for value in values if value is not None)), normalized_entropy(values))


def estimate_novelty(embeddings: Sequence[Embedding | None]) -> float:
    """Mean 1 - maximum cosine similarity; absent vectors are excluded.

    This is an exploratory local-diversity proxy, not a validated novelty measure.
    """
    vectors = [vector for vector in embeddings if vector is not None]
    if len(vectors) < 2:
        return 1.0 if vectors else 0.0
    scores = [(1.0 - max(cosine_similarity(vector, other) for index, other in enumerate(vectors) if index != current)) / 2.0 for current, vector in enumerate(vectors)]
    return sum(scores) / len(scores)


@dataclass(frozen=True, slots=True)
class DqiWeights:
    duplicate_quality: float = 1.0
    coverage: float = 1.0
    entropy: float = 1.0
    novelty: float = 1.0
    difficulty: float = 1.0
    balance: float = 1.0


@dataclass(frozen=True, slots=True)
class DatasetQualityIndex:
    score: float | None
    components: Mapping[str, float | None]
    weights: DqiWeights
    status: str = "computed"
    reason: str | None = None


def calculate_dqi(dataset: Dataset, *, embeddings: Sequence[Embedding | None] | None = None, weights: DqiWeights = DqiWeights()) -> DatasetQualityIndex:
    """Calculate configurable exploratory DQI as a weighted mean of [0,1] components."""
    records = len(dataset.records)
    duplicate_records = sum(len(group.record_indexes) - 1 for group in find_dataset_duplicates(dataset))
    category_values = [record.category for record in dataset.records]
    difficulty_values = [record.difficulty for record in dataset.records]
    coverage = calculate_coverage_statistics(dataset)
    components: dict[str, float | None] = {
        "duplicate_quality": 1.0 - (duplicate_records / records) if records else 0.0,
        "coverage": coverage.prompt_coverage,
        "entropy": normalized_entropy(category_values),
        "novelty": estimate_novelty(embeddings) if embeddings is not None else None,
        "difficulty": normalized_entropy(difficulty_values),
        "balance": analyze_category_balance(dataset).normalized_entropy,
    }
    weight_map = {name: getattr(weights, name) for name in components}
    if any(weight < 0 for weight in weight_map.values()):
        raise ValueError("DQI weights must be non-negative")
    total_weight = sum(weight_map.values())
    if components["novelty"] is None and weight_map["novelty"] > 0:
        return DatasetQualityIndex(None, components, weights, "unavailable", "semantic_embeddings_unavailable")
    score = (sum(float(components[name]) * weight for name, weight in weight_map.items() if weight > 0) / total_weight
             if total_weight else None)
    return DatasetQualityIndex(score, components, weights,
        "computed" if score is not None else "undefined",
        None if score is not None else "total_weight_zero")
