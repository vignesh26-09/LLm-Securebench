"""Exact duplicate identification using normalized SHA-256 prompt fingerprints."""

import hashlib
from collections import defaultdict
from dataclasses import dataclass

from core.dataset.models import Dataset, DatasetRecord
from core.dataset.normalization import normalize_text


def prompt_sha256(prompt: str | None) -> str | None:
    """Return the SHA-256 fingerprint for normalized prompt text, if present."""
    normalized = normalize_text(prompt)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else None


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    sha256: str
    record_indexes: tuple[int, ...]
    record_ids: tuple[str | None, ...]


def find_exact_duplicates(records: tuple[DatasetRecord, ...] | list[DatasetRecord]) -> tuple[DuplicateGroup, ...]:
    """Group records with exactly equal normalized prompts by SHA-256 digest."""
    grouped: dict[str, list[tuple[int, DatasetRecord]]] = defaultdict(list)
    for index, record in enumerate(records):
        digest = prompt_sha256(record.prompt)
        if digest is not None:
            grouped[digest].append((index, record))
    return tuple(
        DuplicateGroup(digest, tuple(index for index, _ in group), tuple(record.id for _, record in group))
        for digest, group in grouped.items()
        if len(group) > 1
    )


def find_dataset_duplicates(dataset: Dataset) -> tuple[DuplicateGroup, ...]:
    """Convenience adapter for duplicate analysis of a complete dataset."""
    return find_exact_duplicates(dataset.records)
