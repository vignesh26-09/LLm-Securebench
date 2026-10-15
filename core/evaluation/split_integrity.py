"""Leakage guards for independent evaluator development and held-out assessment."""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

SPLITS = frozenset({"development", "validation", "test"})


def validate_evaluator_splits(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    """Reject exact and declared related-group leakage across split boundaries.

    Related prompt/near-duplicate grouping is supplied by the study designer. This
    check cannot discover semantic near duplicates on its own.
    """
    if not rows:
        raise ValueError("split manifest has no records")
    ids: set[str] = set()
    groups: dict[str, set[str]] = defaultdict(set)
    counts = {split: 0 for split in SPLITS}
    for row in rows:
        split = row.get("split")
        record_id = row.get("evaluation_id")
        group_id = row.get("related_group_id")
        if split not in SPLITS or not isinstance(record_id, str) or not record_id or not isinstance(group_id, str) or not group_id:
            raise ValueError("split, evaluation_id, and related_group_id are required")
        if record_id in ids:
            raise ValueError("duplicate evaluation ID in split manifest")
        ids.add(record_id)
        groups[group_id].add(split)
        counts[split] += 1
    leaking = sorted(group for group, splits in groups.items() if len(splits) > 1)
    if leaking:
        raise ValueError(f"related groups cross evaluator splits: {', '.join(leaking)}")
    return counts
