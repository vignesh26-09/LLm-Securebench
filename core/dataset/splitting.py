"""Deterministic train/evaluation splitting without ML dependencies."""

import hashlib
from dataclasses import dataclass

from core.dataset.models import Dataset, DatasetRecord


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    train: Dataset
    evaluation: Dataset


def split_train_evaluation(dataset: Dataset, *, evaluation_fraction: float = 0.2, seed: str = "securellmbench") -> DatasetSplit:
    """Split records deterministically by a stable SHA-256 bucket."""
    if not 0.0 < evaluation_fraction < 1.0:
        raise ValueError("evaluation_fraction must be between 0 and 1")
    train: list[DatasetRecord] = []
    evaluation: list[DatasetRecord] = []
    for index, record in enumerate(dataset.records):
        key = record.id or record.prompt or str(index)
        bucket = int.from_bytes(hashlib.sha256(f"{seed}:{key}".encode("utf-8")).digest()[:8], "big") / 2**64
        (evaluation if bucket < evaluation_fraction else train).append(record)
    return DatasetSplit(Dataset(tuple(train), dataset.metadata), Dataset(tuple(evaluation), dataset.metadata))
