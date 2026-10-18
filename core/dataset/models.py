"""Explicit, framework-independent schemas for benchmark datasets."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DatasetRecord:
    """A validated dataset record. All benchmark-specific fields are optional."""

    id: str | None = None
    prompt: str | None = None
    category: str | None = None
    attack_type: str | None = None
    source: str | None = None
    language: str | None = None
    difficulty: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DatasetVersion:
    """Version and provenance information supplied by a dataset publisher."""

    version: str | None = None
    released_at: str | None = None
    checksum: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    """Dataset-level identity and provenance."""

    name: str | None = None
    description: str | None = None
    source: str | None = None
    version: DatasetVersion = field(default_factory=DatasetVersion)
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Dataset:
    """An immutable collection of validated records and its metadata."""

    records: tuple[DatasetRecord, ...]
    metadata: DatasetMetadata = field(default_factory=DatasetMetadata)
