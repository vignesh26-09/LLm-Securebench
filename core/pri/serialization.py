"""Deterministic JSON round-trip for PRI Mode A/B profile infrastructure."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum

from core.pri.models import (
    BenchmarkPopulationIdentity, CoverageMetadata, HierarchyIdentifiers,
    PRIProfileCell, PRIProfileMode, PRIProfileRecord, PRIStatus,
    SystemConfigurationIdentity,
)


def dumps(profile: PRIProfileRecord) -> str:
    return json.dumps(_ready(profile), sort_keys=True, separators=(",", ":"))


def loads(payload: str) -> PRIProfileRecord:
    value = json.loads(payload)
    configuration_data = dict(value["configuration"])
    configuration_data["seeds"] = tuple(configuration_data.get("seeds", ()))
    configuration = SystemConfigurationIdentity(**configuration_data)
    population_data = dict(value["population"])
    population_data["requested_categories"] = tuple(population_data.get("requested_categories", ()))
    population_data["observed_categories"] = tuple(population_data.get("observed_categories", ()))
    population = BenchmarkPopulationIdentity(**population_data)
    cells = tuple(_cell(item) for item in value["cells"])
    coverage = _coverage(value.get("coverage"))
    return PRIProfileRecord(configuration, population, PRIProfileMode(value["mode"]), cells, tuple(value.get("benchmark_run_ids", ())), coverage, PRIStatus(value["status"]), value.get("provenance", {}), tuple(value.get("warnings", ())), tuple(value.get("errors", ())), value["schema_version"], value.get("scalar_pri"))


def _cell(value: dict[str, object]) -> PRIProfileCell:
    data = dict(value)
    data["status"] = PRIStatus(data["status"])
    data["hierarchy"] = HierarchyIdentifiers(**data["hierarchy"])
    data["warnings"] = tuple(data.get("warnings", ()))
    return PRIProfileCell(**data)


def _coverage(value: object) -> CoverageMetadata | None:
    if value is None:
        return None
    data = dict(value)
    data["requested_categories"] = tuple(data["requested_categories"])
    data["observed_categories"] = tuple(data["observed_categories"])
    data["category_statuses"] = {key: PRIStatus(item) for key, item in data.get("category_statuses", {}).items()}
    return CoverageMetadata(**data)


def _ready(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_ready(item) for item in value]
    return value
