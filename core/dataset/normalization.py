"""Conservative text normalization used before duplicate analysis."""

import re
import unicodedata

from core.dataset.models import Dataset, DatasetRecord

_HORIZONTAL_WHITESPACE = re.compile(r"[^\S\r\n]+")


def normalize_text(value: str | None) -> str | None:
    """Apply Unicode NFC, normalized line endings, and conservative whitespace cleanup."""
    if value is None:
        return None
    value = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(_HORIZONTAL_WHITESPACE.sub(" ", line).strip() for line in value.split("\n")).strip()


class TextNormalizer:
    """Normalizes text fields while preserving optional fields and metadata."""

    _fields = ("id", "prompt", "category", "attack_type", "source", "language", "difficulty")

    def process(self, dataset: Dataset) -> Dataset:
        records = tuple(
            DatasetRecord(
                **{field: normalize_text(getattr(record, field)) for field in self._fields},
                metadata=record.metadata,
            )
            for record in dataset.records
        )
        return Dataset(records=records, metadata=dataset.metadata)
