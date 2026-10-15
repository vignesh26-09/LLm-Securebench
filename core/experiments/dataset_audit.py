"""Eligibility checks for future research attack-execution manifests.

Near-duplicate matching is a conservative review flag, not semantic proof.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Mapping, Sequence

SPLITS = frozenset({"development", "validation", "test"})


def audit_research_manifest(manifest: Mapping[str, object], source: Path,
                            *, near_duplicate_ratio: float = 0.9) -> dict[str, object]:
    required = ("dataset_id", "version", "source_revision", "license", "source_sha256", "cases")
    if any(not manifest.get(key) for key in required):
        raise ValueError("research dataset manifest lacks source identity, license, or cases")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest["source_sha256"]:
        raise ValueError("research dataset source checksum mismatch")
    rows = manifest["cases"]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("research cases must be a sequence")
    ids: set[str] = set()
    groups: dict[str, set[str]] = defaultdict(set)
    split_counts: Counter[str] = Counter()
    prompt_groups: dict[str, set[str]] = defaultdict(set)
    normalized: list[tuple[str, str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("research case must be a mapping")
        keys = ("case_id", "legitimate_task", "attack_objective", "attack_category",
                "related_group_id", "split", "prompt")
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in keys):
            raise ValueError("research case lacks identity, task, objective, category, split, or prompt")
        if row["split"] not in SPLITS or row["case_id"] in ids:
            raise ValueError("invalid research split or duplicate case ID")
        ids.add(row["case_id"])
        groups[row["related_group_id"]].add(row["split"])
        split_counts[row["split"]] += 1
        prompt = re.sub(r"\s+", " ", row["prompt"].casefold()).strip()
        prompt_groups[prompt].add(row["split"])
        normalized.append((row["case_id"], row["split"], prompt))
    if not ids:
        raise ValueError("research dataset has no eligible cases")
    if any(len(splits) > 1 for splits in groups.values()):
        raise ValueError("related group crosses research splits")
    if any(len(splits) > 1 for splits in prompt_groups.values()):
        raise ValueError("exact prompt duplicate crosses research splits")
    flags = []
    for index, (left_id, left_split, left_prompt) in enumerate(normalized):
        for right_id, right_split, right_prompt in normalized[index + 1:]:
            if left_split != right_split and SequenceMatcher(None, left_prompt, right_prompt).ratio() >= near_duplicate_ratio:
                flags.append({"left_case_id": left_id, "right_case_id": right_id,
                              "reason": "lexical_near_duplicate_cross_split_review_required"})
    return {"status": "review_required" if flags else "structurally_eligible",
            "source_sha256": digest, "case_count": len(ids),
            "split_counts": dict(split_counts), "near_duplicate_flags": flags,
            "note": "No semantic duplicate or scientific suitability guarantee"}
