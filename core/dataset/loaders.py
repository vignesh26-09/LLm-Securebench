"""Built-in JSON, JSONL, and CSV adapters for the dataset loader port."""

import csv
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from core.dataset.models import Dataset, DatasetMetadata, DatasetVersion
from core.dataset.validation import DatasetValidationError, DatasetValidator


class _BaseDatasetLoader:
    def __init__(self, validator: DatasetValidator | None = None) -> None:
        self._validator = validator or DatasetValidator()

    def _dataset(self, records: Iterable[Mapping[str, Any]], metadata: Mapping[str, Any] | None = None) -> Dataset:
        validated = tuple(self._validator.validate_record(record, row_number=index) for index, record in enumerate(records, start=1))
        return Dataset(records=validated, metadata=_parse_metadata(metadata or {}))


class JsonDatasetLoader(_BaseDatasetLoader):
    def load(self, path: Path) -> Dataset:
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
        if isinstance(value, list):
            return self._dataset(value)
        if not isinstance(value, Mapping) or not isinstance(value.get("records"), list):
            raise DatasetValidationError("JSON dataset must be a record list or an object with a records list")
        return self._dataset(value["records"], value.get("metadata"))


class JsonlDatasetLoader(_BaseDatasetLoader):
    def load(self, path: Path) -> Dataset:
        records: list[Mapping[str, Any]] = []
        with path.open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise DatasetValidationError(f"Line {line_number}: invalid JSON") from error
                if not isinstance(value, Mapping):
                    raise DatasetValidationError(f"Line {line_number}: record must be an object")
                records.append(value)
        return self._dataset(records)


class CsvDatasetLoader(_BaseDatasetLoader):
    def load(self, path: Path) -> Dataset:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise DatasetValidationError("CSV dataset must include a header row")
            records = []
            for row in reader:
                record = {key: value for key, value in row.items() if value not in (None, "")}
                if "metadata" in record:
                    try:
                        record["metadata"] = json.loads(record["metadata"])
                    except json.JSONDecodeError as error:
                        raise DatasetValidationError("CSV metadata must be valid JSON") from error
                records.append(record)
        return self._dataset(records)


def _parse_metadata(value: Mapping[str, Any]) -> DatasetMetadata:
    if not isinstance(value, Mapping):
        raise DatasetValidationError("dataset metadata must be an object")
    version_value = value.get("version", {})
    if isinstance(version_value, str):
        version = DatasetVersion(version=version_value)
    elif isinstance(version_value, Mapping):
        allowed = {"version", "released_at", "checksum"}
        unknown = set(version_value) - allowed
        if unknown:
            raise DatasetValidationError(f"unknown version fields: {', '.join(sorted(unknown))}")
        version = DatasetVersion(**dict(version_value))
    else:
        raise DatasetValidationError("dataset version must be a string or object")
    known = {"name", "description", "source", "version"}
    return DatasetMetadata(
        name=value.get("name"), description=value.get("description"), source=value.get("source"),
        version=version, extra={key: item for key, item in value.items() if key not in known},
    )
