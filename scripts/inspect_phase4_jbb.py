"""Offline metadata-only audit of pinned JBB behaviors and attack artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEHAVIORS = ROOT / "data" / "external" / "jbb_behaviors_886acc3"
ARTIFACTS = ROOT / "data" / "external" / "jbb_artifacts_909e68c"
CALIBRATION = ROOT / "data" / "external" / "jailbreakbench_judge_comparison_b2b462fd.csv"
PINNED = {
    BEHAVIORS / "harmful-behaviors.csv": "4a8ec6832056b631eb092dccc60d37a61c3d441268268888b3d006288afeffa1",
    BEHAVIORS / "benign-behaviors.csv": "3cda234d21a991fa309bbfea4b6d9dae31ccdf8e9d452424b6a983e4fdc33468",
    ARTIFACTS / "PAIR-black_box-vicuna-13b-v1.5.json": "18b101386419a98fbdf45cb987069f83af3a40d5e0f7f0d32c4e9dc5ecc049b4",
    ARTIFACTS / "GCG-transfer-gpt-3.5-turbo-1106.json": "ff185b1dc73732d830e96efdb3f4a92294ee72e9c88a1800b1d11d4ecb3d4cdf",
    ARTIFACTS / "JBC-manual-vicuna-13b-v1.5.json": "1d5df5aa451c3d1bb8a4c048a7b2e1e6132e72f2970cb9d94ffc77f44e0edb39",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def audit() -> dict[str, object]:
    for path, digest in PINNED.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"pinned source hash mismatch: {path.name}")
    harmful = _rows(BEHAVIORS / "harmful-behaviors.csv")
    benign = _rows(BEHAVIORS / "benign-behaviors.csv")
    expected_columns = {"Index", "Goal", "Target", "Behavior", "Category", "Source"}
    if len(harmful) != 100 or len(benign) != 100:
        raise ValueError("unexpected JBB behavior row count")
    for name, rows in (("harmful", harmful), ("benign", benign)):
        if set(rows[0]) != expected_columns or len({row["Index"] for row in rows}) != 100:
            raise ValueError(f"{name} schema or case IDs invalid")
        if len({_normalized(row["Goal"]) for row in rows}) != 100:
            raise ValueError(f"{name} has exact duplicate goals")
    artifacts = {}
    for path in PINNED:
        if path.suffix != ".json":
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        rows = value["jailbreaks"]
        if len(rows) != 100 or len({str(row["index"]) for row in rows}) != 100:
            raise ValueError(f"artifact row count or IDs invalid: {path.name}")
        artifacts[path.name] = {str(row["index"]): row for row in rows}
    eligible = []
    rejected = Counter()
    for row in harmful:
        index = row["Index"]
        candidates = [artifact.get(index) for artifact in artifacts.values()]
        if all(item and isinstance(item.get("prompt"), str) and item["prompt"].strip()
               and _normalized(item.get("goal", "")) == _normalized(row["Goal"])
               and item.get("category") == row["Category"]
               for item in candidates):
            eligible.append({"index": index, "category": row["Category"],
                             "source": row["Source"],
                             "attack_prompt_lengths": [len(item["prompt"]) for item in candidates]})
        else:
            rejected[row["Category"]] += 1
    calibration = _rows(CALIBRATION)
    calibration_goals = {_normalized(row["goal"]) for row in calibration}
    harmful_overlap = [row["Index"] for row in harmful
                       if _normalized(row["Goal"]) in calibration_goals]
    harmful_near_pairs = []
    for left_number, left in enumerate(harmful):
        for right in harmful[left_number + 1:]:
            if SequenceMatcher(None, _normalized(left["Goal"]), _normalized(right["Goal"])).ratio() >= 0.9:
                harmful_near_pairs.append([left["Index"], right["Index"]])
    calibration_near_overlap = [row["Index"] for row in harmful
                                if any(SequenceMatcher(None, _normalized(row["Goal"]), goal).ratio() >= 0.9
                                       for goal in calibration_goals)]
    cross_kind_overlap = len({_normalized(row["Goal"]) for row in harmful} &
                             {_normalized(row["Goal"]) for row in benign})
    return {
        "dataset_revision": "886acc352a31533ffbcf4ef22c744658688086fc",
        "artifact_revision": "909e68c01d94222b8ad2e397a017e2e12e2adb73",
        "harmful_rows": len(harmful), "benign_rows": len(benign),
        "harmful_categories": dict(Counter(row["Category"] for row in harmful)),
        "artifact_complete_matching_indices": eligible,
        "artifact_missing_or_mismatched_by_category": dict(rejected),
        "historical_calibration_goal_overlap_indices": harmful_overlap,
        "historical_calibration_goal_overlap_count": len(harmful_overlap),
        "historical_calibration_near_overlap_indices": calibration_near_overlap,
        "historical_calibration_near_overlap_count": len(calibration_near_overlap),
        "harmful_goal_lexical_near_duplicate_pairs": harmful_near_pairs,
        "harmful_benign_exact_goal_overlap": cross_kind_overlap,
        "source_hashes": {str(path.relative_to(ROOT)): digest for path, digest in PINNED.items()},
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"artifact_complete_matching_indices", "historical_calibration_goal_overlap_indices"}},
                     sort_keys=True))
