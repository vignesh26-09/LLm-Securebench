"""Immutable profile-first PRI contracts without category estimators or ranking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


PRI_SCHEMA_VERSION = "pri-profile-v1"


class PRIProfileMode(StrEnum):
    EVIDENCE_ASSEMBLY = "mode_a_profile_assembly"
    DESCRIPTIVE_DIAGNOSTICS = "mode_b_descriptive_diagnostics"


class PRIStatus(StrEnum):
    APPLICABLE = "applicable"
    NOT_EVALUATED = "not_evaluated"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"
    SKIPPED = "skipped"
    REFUSED = "refused"
    INSUFFICIENT_DATA = "insufficient_data"
    UNDEFINED = "undefined"
    UNAVAILABLE = "unavailable"
    UNCALIBRATED = "uncalibrated"
    INCOMPATIBLE = "incompatible"
    ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class SystemConfigurationIdentity:
    model_id: str | None
    provider: str | None
    model_version: str | None
    generation: Mapping[str, object] = field(default_factory=dict)
    seeds: tuple[int, ...] = ()
    system_context_id: str | None = None
    developer_context_id: str | None = None
    harness_id: str | None = None
    tooling_id: str | None = None
    policy_id: str | None = None
    taxonomy_id: str | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BenchmarkPopulationIdentity:
    benchmark_id: str | None
    benchmark_version: str | None
    benchmark_hash: str | None
    dataset_id: str | None
    dataset_version: str | None
    taxonomy_version: str | None
    threat_model: str | None
    requested_categories: tuple[str, ...] = ()
    observed_categories: tuple[str, ...] = ()
    evaluation_configuration: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HierarchyIdentifiers:
    category: str | None = None
    attack_family_id: str | None = None
    base_case_id: str | None = None
    prompt_variant_id: str | None = None
    stochastic_run_id: str | None = None
    session_id: str | None = None
    sequence_id: str | None = None
    attack_instance_id: str | None = None


@dataclass(frozen=True, slots=True)
class PRIProfileCell:
    benchmark_category: str | None
    observed_construct: str | None
    source_namespace: str
    source_feature_name: str
    value: object | None
    value_type: str
    units: str | None
    orientation: str | None
    status: PRIStatus
    status_reason: str | None = None
    uncertainty: Mapping[str, object] | None = None
    confidence: float | None = None
    hierarchy: HierarchyIdentifiers = field(default_factory=HierarchyIdentifiers)
    provenance: Mapping[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_namespace or not self.source_feature_name or not self.value_type:
            raise ValueError("PRI cells require source namespace, feature name, and value type")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        json.dumps(self.value)


@dataclass(frozen=True, slots=True)
class CoverageMetadata:
    requested_categories: tuple[str, ...]
    observed_categories: tuple[str, ...]
    category_statuses: Mapping[str, PRIStatus] = field(default_factory=dict)
    hierarchy_counts: Mapping[str, int] = field(default_factory=dict)
    cell_status_counts: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PRIProfileRecord:
    configuration: SystemConfigurationIdentity
    population: BenchmarkPopulationIdentity
    mode: PRIProfileMode
    cells: tuple[PRIProfileCell, ...] = ()
    benchmark_run_ids: tuple[str, ...] = ()
    coverage: CoverageMetadata | None = None
    status: PRIStatus = PRIStatus.UNCALIBRATED
    provenance: Mapping[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    schema_version: str = PRI_SCHEMA_VERSION
    scalar_pri: None = None

    def __post_init__(self) -> None:
        if self.status is not PRIStatus.UNCALIBRATED or self.scalar_pri is not None:
            raise ValueError("PRI Mode A/B profiles must be uncalibrated and have no scalar PRI")


@dataclass(frozen=True, slots=True)
class PRIReferenceArtifact:
    artifact_id: str
    methodology_version: str
    benchmark_hash: str | None
    taxonomy_version: str | None
    threat_model: str | None
    category_definitions: Mapping[str, object] = field(default_factory=dict)
    approved_category_estimators: Mapping[str, object] = field(default_factory=dict)
    configuration_requirements: Mapping[str, object] = field(default_factory=dict)
    reference_population: Mapping[str, object] = field(default_factory=dict)
    normalization: Mapping[str, object] = field(default_factory=dict)
    weighting_policy: Mapping[str, object] = field(default_factory=dict)
    missingness_policy: Mapping[str, object] = field(default_factory=dict)
    stochastic_run_policy: Mapping[str, object] = field(default_factory=dict)
    hierarchy_resampling_policy: Mapping[str, object] = field(default_factory=dict)
    uncertainty_method: str | None = None
    validation_status: str = "unvalidated"
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifact_id or not self.methodology_version:
            raise ValueError("PRI reference artifact requires identity and methodology version")
