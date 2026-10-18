"""Mode A profile assembly from original artifacts or DRAA evidence transport."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Iterable

from core.draa.models import DRAAEvidenceRecord, DRAAStatus, EvidenceFeature
from core.pri.models import (
    BenchmarkPopulationIdentity, CoverageMetadata, HierarchyIdentifiers,
    PRIProfileCell, PRIProfileMode, PRIProfileRecord, PRIStatus,
    SystemConfigurationIdentity,
)


class PRIProfileBuilder:
    def build(self, configuration: SystemConfigurationIdentity, population: BenchmarkPopulationIdentity, *, mode: PRIProfileMode = PRIProfileMode.EVIDENCE_ASSEMBLY, cells: Iterable[PRIProfileCell] = (), draa_records: Iterable[DRAAEvidenceRecord] = (), benchmark_run_ids: Iterable[str] = (), provenance: dict[str, object] | None = None) -> PRIProfileRecord:
        output = list(cells)
        seen = {_provenance_key(cell.provenance) for cell in output}
        warnings: list[str] = []
        for record in draa_records:
            for feature in record.features:
                cell = _cell_from_draa(record, feature)
                key = _provenance_key(cell.provenance)
                if key in seen and key:
                    warnings.append("duplicate_upstream_provenance")
                    continue
                seen.add(key)
                output.append(cell)
        observed = tuple(sorted({cell.benchmark_category for cell in output if cell.benchmark_category is not None}))
        population = replace(population, observed_categories=observed or population.observed_categories)
        coverage = _coverage(population, output)
        return PRIProfileRecord(configuration, population, mode, tuple(output), tuple(benchmark_run_ids), coverage, provenance=dict(provenance or {}), warnings=tuple(sorted(set(warnings))))


def _cell_from_draa(record: DRAAEvidenceRecord, feature: EvidenceFeature) -> PRIProfileCell:
    hierarchy_data = feature.provenance.get("hierarchy") if isinstance(feature.provenance.get("hierarchy"), dict) else {}
    hierarchy = HierarchyIdentifiers(**{key: hierarchy_data.get(key) for key in HierarchyIdentifiers.__dataclass_fields__})
    return PRIProfileCell(feature.provenance.get("benchmark_category") if isinstance(feature.provenance.get("benchmark_category"), str) else None, feature.provenance.get("observed_construct") if isinstance(feature.provenance.get("observed_construct"), str) else None, feature.namespace, feature.name, feature.raw_value, feature.value_type, feature.units, feature.orientation, _status(feature.status), feature.status_reason, _uncertainty(feature.uncertainty), feature.confidence, hierarchy, {**dict(feature.provenance), "draa_schema_version": record.schema_version, "draa_status": record.status.value, "draa_risk_score": record.risk_score})


def _status(value: DRAAStatus) -> PRIStatus:
    aliases = {"applicable": PRIStatus.APPLICABLE, "not_applicable": PRIStatus.NOT_APPLICABLE, "failed": PRIStatus.FAILED, "skipped": PRIStatus.SKIPPED, "refused": PRIStatus.REFUSED, "insufficient_data": PRIStatus.INSUFFICIENT_DATA, "undefined": PRIStatus.UNDEFINED, "uncalibrated": PRIStatus.UNCALIBRATED, "incompatible": PRIStatus.INCOMPATIBLE, "absent": PRIStatus.ABSENT}
    return aliases[value.value]


def _uncertainty(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    return {name: getattr(value, name) for name in ("confidence_interval", "standard_error", "bootstrap_interval", "reason")}


def _coverage(population: BenchmarkPopulationIdentity, cells: list[PRIProfileCell]) -> CoverageMetadata:
    requested = population.requested_categories
    observed = population.observed_categories
    statuses = {category: (PRIStatus.APPLICABLE if category in observed else PRIStatus.NOT_EVALUATED) for category in requested}
    fields = ("attack_family_id", "base_case_id", "prompt_variant_id", "stochastic_run_id", "session_id", "sequence_id", "attack_instance_id")
    counts = {field: len({getattr(cell.hierarchy, field) for cell in cells if getattr(cell.hierarchy, field) is not None}) for field in fields}
    counts["categories"] = len(observed)
    return CoverageMetadata(requested, observed, statuses, counts, dict(Counter(cell.status.value for cell in cells)))


def _provenance_key(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    for key in ("artifact_id", "evaluation_id", "source_result_id"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
    return None
