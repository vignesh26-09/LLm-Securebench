"""Deterministic grouped-holdout split construction."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import replace
from typing import Iterable

from core.prediction.models import FeatureSchema, HierarchyIdentifiers, SplitManifest, SplitPolicy, SplitStrategy, TargetRecord


def build_grouped_manifest(*, manifest_id: str, policy: SplitPolicy, target_schema_version: str, feature_schema: FeatureSchema, targets: Iterable[TargetRecord], dataset_identity: dict[str, object] | None = None, benchmark_identity: dict[str, object] | None = None, provenance: dict[str, object] | None = None) -> SplitManifest:
    """Assign whole configured groups, never individual repeated runs, to partitions."""
    records = tuple(targets)
    if policy.strategy is not SplitStrategy.GROUPED_HOLDOUT:
        raise ValueError("only grouped holdout is supported for Phase 9B")
    group_key = policy.grouping_keys[0]
    grouped: dict[str, list[str]] = defaultdict(list)
    for record in records:
        group = _hierarchy_value(record.hierarchy, group_key)
        if group is None:
            raise ValueError(f"required grouping value unavailable: {group_key}")
        grouped[group].append(record.unit_id)
    groups = sorted(grouped)
    random.Random(policy.seed).shuffle(groups)
    partitions = _allocate(groups, policy)
    group_partitions = {group: partition for partition, values in partitions.items() for group in values}
    unit_partitions = {unit: group_partitions[group] for group, units in grouped.items() for unit in units}
    return SplitManifest(manifest_id, policy.policy_id, policy.version, target_schema_version, feature_schema.version, feature_schema.schema_hash, group_key, unit_partitions, group_partitions, policy.seed, dataset_identity or {}, benchmark_identity or {}, provenance or {})


def _allocate(groups: list[str], policy: SplitPolicy) -> dict[str, list[str]]:
    fractions = policy.partition_fractions or {partition: 1.0 for partition in policy.requested_partitions}
    total = sum(fractions.values())
    desired = {name: len(groups) * fractions[name] / total for name in policy.requested_partitions}
    counts = {name: int(desired[name]) for name in policy.requested_partitions}
    for name in sorted(policy.requested_partitions, key=lambda item: (desired[item] - counts[item], item), reverse=True)[: len(groups) - sum(counts.values())]:
        counts[name] += 1
    result: dict[str, list[str]] = {}
    offset = 0
    for partition in policy.requested_partitions:
        result[partition] = groups[offset : offset + counts[partition]]
        offset += counts[partition]
    return result


def _hierarchy_value(hierarchy: HierarchyIdentifiers, key: str) -> str | None:
    if key not in HierarchyIdentifiers.__dataclass_fields__:
        raise ValueError(f"unknown hierarchy grouping key: {key}")
    return getattr(hierarchy, key)
