"""Balanced, without-replacement engineering pilots from the pinned corpus."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Mapping, Sequence

from core.dataset.benchmark_catalog import BenchmarkSelection, LARGE_KEY


PILOT_CASES = 50
PER_CATEGORY = 25
QUICK_CASES = 10
CATEGORIES = ("benign_control_source", "red_team_source_seed")


@dataclass(frozen=True)
class PilotAllocation:
    indices: tuple[int, ...]
    cycle: int
    selection_sha256: str


def allocate_pilot(selection: BenchmarkSelection, prior: Sequence[Mapping[str, object]]) -> PilotAllocation:
    """Draw 25 from each source class, without reuse within a 200-run cycle.

    The caller serializes allocation with new-job admission and persists the
    chosen indices before executing model calls. Prior runs from other corpus
    versions do not enter the supplied allocation history.
    """
    return allocate_rotating(selection, prior, PER_CATEGORY)


def allocate_rotating(selection: BenchmarkSelection, prior: Sequence[Mapping[str, object]], per_category: int) -> PilotAllocation:
    if per_category not in {5, PER_CATEGORY}:
        raise ValueError("Unsupported rotating sample size")
    if selection.key != LARGE_KEY or selection.count != 10000:
        raise ValueError("Pilot allocation requires the complete verified corpus")
    groups = {category: [index for index, row in enumerate(selection.dataset.records)
                         if row.category == category] for category in CATEGORIES}
    if any(len(group) != 5000 for group in groups.values()):
        raise ValueError("Pilot corpus must contain 5,000 records per source class")
    valid = [entry for entry in prior if isinstance(entry.get("sample_cycle"), int)
             and isinstance(entry.get("sample_indices"), list)
             and len(entry["sample_indices"]) == per_category * 2]
    cycle = max((entry["sample_cycle"] for entry in valid), default=0)
    used = {index for entry in valid if entry["sample_cycle"] == cycle
            for index in entry["sample_indices"] if type(index) is int}
    available = {category: [index for index in group if index not in used]
                 for category, group in groups.items()}
    if any(len(group) < per_category for group in available.values()):
        cycle += 1
        available = groups
    chooser = secrets.SystemRandom()
    indices = tuple(sorted(index for category in CATEGORIES
                           for index in chooser.sample(available[category], per_category)))
    digest = hashlib.sha256(json.dumps(indices, separators=(",", ":")).encode()).hexdigest()
    return PilotAllocation(indices, cycle, digest)
