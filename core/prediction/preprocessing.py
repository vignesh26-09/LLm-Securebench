"""Small training-only numeric/categorical preprocessing for Phase 9B."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Iterable

from core.prediction.models import FeatureRecord, FeatureSchema, SemanticStatus


@dataclass(frozen=True, slots=True)
class PreprocessingConfig:
    scale_numeric: bool = True
    numeric_imputation: str = "mean"
    categorical_unknown_value: str = "__unknown__"


@dataclass(frozen=True, slots=True)
class FittedPreprocessor:
    schema_hash: str
    config: PreprocessingConfig
    numeric_means: dict[str, float]
    numeric_scales: dict[str, float]
    categories: dict[str, tuple[str, ...]]
    output_names: tuple[str, ...]

    def transform(self, records: Iterable[FeatureRecord]) -> dict[str, tuple[float, ...]]:
        indexed = _index(records)
        output: dict[str, tuple[float, ...]] = {}
        for unit_id, values in indexed.items():
            row: list[float] = []
            for name in sorted(self.numeric_means):
                record = values.get(name)
                missing = record is None or record.status is not SemanticStatus.AVAILABLE
                value = self.numeric_means[name] if missing else _numeric(record.raw_value, name)
                if self.config.scale_numeric:
                    value = (value - self.numeric_means[name]) / self.numeric_scales[name]
                row.extend((value, 1.0 if missing else 0.0))
            for name in sorted(self.categories):
                record = values.get(name)
                category = self.config.categorical_unknown_value if record is None or record.status is not SemanticStatus.AVAILABLE else str(record.raw_value)
                row.extend(1.0 if category == known else 0.0 for known in self.categories[name])
            output[unit_id] = tuple(row)
        return output


def fit_preprocessor(schema: FeatureSchema, training_records: Iterable[FeatureRecord], config: PreprocessingConfig = PreprocessingConfig()) -> FittedPreprocessor:
    indexed = _index(training_records)
    numeric: dict[str, list[float]] = {item.name: [] for item in schema.features if item.expected_type == "numeric"}
    categorical: dict[str, set[str]] = {item.name: set() for item in schema.features if item.expected_type == "categorical"}
    for values in indexed.values():
        for name in numeric:
            record = values.get(name)
            if record is not None and record.status is SemanticStatus.AVAILABLE:
                numeric[name].append(_numeric(record.raw_value, name))
        for name in categorical:
            record = values.get(name)
            if record is not None and record.status is SemanticStatus.AVAILABLE:
                categorical[name].add(str(record.raw_value))
    means = {name: mean(values) if values else 0.0 for name, values in numeric.items()}
    scales = {name: (pstdev(values) if len(values) > 1 and pstdev(values) > 0 else 1.0) for name, values in numeric.items()}
    categories = {name: tuple(sorted(values | {config.categorical_unknown_value})) for name, values in categorical.items()}
    output_names = tuple(item for name in sorted(numeric) for item in (f"{name}__value", f"{name}__missing")) + tuple(f"{name}={category}" for name in sorted(categories) for category in categories[name])
    return FittedPreprocessor(schema.schema_hash, config, means, scales, categories, output_names)


def _index(records: Iterable[FeatureRecord]) -> dict[str, dict[str, FeatureRecord]]:
    output: dict[str, dict[str, FeatureRecord]] = {}
    for record in records:
        output.setdefault(record.unit_id, {})[record.feature_name] = record
    return output


def _numeric(value: object | None, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"numeric feature {name} must have a finite numeric value")
    return float(value)
