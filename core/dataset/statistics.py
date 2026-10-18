"""Basic descriptive statistics for loaded datasets."""

from collections import Counter
from dataclasses import dataclass

from core.dataset.models import Dataset


@dataclass(frozen=True, slots=True)
class DatasetStatistics:
    record_count: int
    prompt_count: int
    missing_field_counts: dict[str, int]
    category_counts: dict[str, int]
    attack_type_counts: dict[str, int]
    language_counts: dict[str, int]


def calculate_dataset_statistics(dataset: Dataset) -> DatasetStatistics:
    """Calculate non-research descriptive statistics for a dataset."""
    fields = ("id", "prompt", "category", "attack_type", "source", "language", "difficulty")
    missing = {field: sum(getattr(record, field) is None for record in dataset.records) for field in fields}
    def counts(field: str) -> dict[str, int]:
        return dict(Counter(value for record in dataset.records if (value := getattr(record, field)) is not None))
    return DatasetStatistics(len(dataset.records), len(dataset.records) - missing["prompt"], missing, counts("category"), counts("attack_type"), counts("language"))
