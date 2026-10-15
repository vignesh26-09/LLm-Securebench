"""Describe the candidate production source pool; do not assign frozen splits."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __package__:
    from scripts.inspect_phase4_jbb import audit
else:
    from inspect_phase4_jbb import audit


def report() -> dict[str, object]:
    source = audit()
    near = set(source["historical_calibration_near_overlap_indices"])
    pilot = {"1", "51"}
    aligned = source["artifact_complete_matching_indices"]
    eligible = [row for row in aligned if row["index"] not in near | pilot]
    categories = dict(sorted(Counter(row["category"] for row in eligible).items()))
    if len(eligible) != 66 or any(count < 5 for count in categories.values()):
        raise ValueError("candidate pool no longer supports proposed four-per-category test split")
    return {"status": "candidate_pool_not_frozen_split",
            "dataset_revision": source["dataset_revision"],
            "artifact_revision": source["artifact_revision"],
            "aligned_source_goals": len(aligned),
            "historical_calibration_near_overlap_ids": sorted(near, key=int),
            "used_exploratory_pilot_ids": sorted(pilot, key=int),
            "candidate_goal_ids": sorted((row["index"] for row in eligible), key=int),
            "candidate_goal_count": len(eligible),
            "candidate_by_category": categories,
            "proposed_split_counts": {"development": 10, "validation": 16, "test": 40},
            "exact_split_frozen": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_goal_count": result["candidate_goal_count"],
                      "exact_split_frozen": False}, sort_keys=True))
