"""Validation at the ingestion boundary."""

from dataclasses import dataclass
from typing import Any, Mapping

from core.dataset.models import DatasetRecord

RECORD_FIELDS = frozenset({"id", "prompt", "category", "attack_type", "source", "language", "difficulty", "metadata"})
TEXT_FIELDS = RECORD_FIELDS - {"metadata"}


class DatasetValidationError(ValueError):
    """Raised when external data cannot be represented as a dataset record."""


@dataclass(frozen=True, slots=True)
class DatasetValidator:
    """Converts untrusted mappings to explicit dataset schemas."""

    def validate_record(self, value: Mapping[str, Any], *, row_number: int | None = None) -> DatasetRecord:
        if not isinstance(value, Mapping):
            raise DatasetValidationError(self._message("record must be an object", row_number))
        unknown = set(value) - RECORD_FIELDS
        if unknown:
            raise DatasetValidationError(self._message(f"unknown fields: {', '.join(sorted(unknown))}", row_number))
        parsed: dict[str, str | None] = {}
        for field in TEXT_FIELDS:
            field_value = value.get(field)
            if field_value is not None and not isinstance(field_value, str):
                raise DatasetValidationError(self._message(f"{field} must be a string or null", row_number))
            parsed[field] = field_value
        metadata = value.get("metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, Mapping):
            raise DatasetValidationError(self._message("metadata must be an object", row_number))
        if not parsed["id"] and not parsed["prompt"]:
            raise DatasetValidationError(self._message("record requires at least an id or prompt", row_number))
        return DatasetRecord(metadata=dict(metadata), **parsed)

    @staticmethod
    def _message(message: str, row_number: int | None) -> str:
        return f"Row {row_number}: {message}" if row_number is not None else message
