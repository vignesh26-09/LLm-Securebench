"""Prepare a blinded disagreement handoff from two completed human forms.

Does not judge responses or change reviewer submissions. The output directory
must not exist, so a prior handoff cannot be overwritten.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.evaluation.phase5_annotation import audit_annotation_batch, judgments_from_forms
from scripts.import_phase5_annotation import verify_package

REVIEW_FIELDS = ("sample_id", "legitimate_task", "adversarial_objective",
                 "context_before_response", "target_response", "reviewer_a_outcome",
                 "reviewer_a_rationale", "reviewer_b_outcome", "reviewer_b_rationale")
DECISION_FIELDS = ("sample_id", "adjudicator_id", "outcome", "rationale")


def prepare(*, phase4: Path, package: Path, reviewer_a: Path, reviewer_b: Path,
            output_dir: Path) -> dict[str, object]:
    restricted = phase4 / "restricted_annotation"
    public_path = restricted / "blinded_batch_v1.json"
    private_path = restricted / "private_join_map_v1.json"
    audit = audit_annotation_batch(
        observations_dir=phase4 / "jbb_pilot_run_v1" / "observations",
        objectives_path=phase4 / "jbb_annotation_objectives_v1.json",
        candidates_path=restricted / "candidates_v1.json",
        public_path=public_path, private_path=private_path)
    provenance = verify_package(package, public_path=public_path,
        private_path=private_path, batch_id=str(audit["batch_id"]),
        sample_count=int(audit["blinded_sample_count"]))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    judgments = judgments_from_forms(public, reviewer_a, reviewer_b)
    review_rows = disagreement_rows(public, judgments)
    by_sample = {row["sample_id"] for row in judgments}
    output_dir.mkdir(parents=True, exist_ok=False)
    review_path = output_dir / "disagreement_context.csv"
    decision_path = output_dir / "adjudication_to_complete.csv"
    with review_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(review_rows)
    with decision_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows({"sample_id": row["sample_id"]} for row in review_rows)
    return {"batch_id": audit["batch_id"], "reviewed_samples": len(by_sample),
            "disagreements": len(review_rows),
            "disagreement_sample_ids": [row["sample_id"] for row in review_rows],
            "reviewer_a_sha256": hashlib.sha256(reviewer_a.read_bytes()).hexdigest(),
            "reviewer_b_sha256": hashlib.sha256(reviewer_b.read_bytes()).hexdigest(),
            "package_manifest_sha256": provenance["package_manifest_sha256"],
            "context_csv": str(review_path), "decision_csv": str(decision_path)}


def disagreement_rows(public: dict, judgments: list[dict[str, str]]) -> list[dict[str, str]]:
    """Use locked independent judgments only; never infer adjudicated outcomes."""
    by_sample: dict[str, list[dict[str, str]]] = {}
    for row in judgments:
        by_sample.setdefault(row["sample_id"], []).append(row)
    items = {item["sample_id"]: item for item in public["items"]}
    review_rows = []
    for sample_id in sorted(by_sample):
        a, b = by_sample[sample_id]
        if a["outcome"] == b["outcome"]:
            continue
        item = items[sample_id]
        history = item["conversation_history"]
        if history and history[-1] == {"role": "assistant", "content": item["target_response"]}:
            history = history[:-1]
        review_rows.append({
            "sample_id": sample_id,
            "legitimate_task": item["legitimate_task"],
            "adversarial_objective": item["adversarial_objective"],
            "context_before_response": json.dumps(history, ensure_ascii=False),
            "target_response": item["target_response"],
            "reviewer_a_outcome": a["outcome"], "reviewer_a_rationale": a["rationale"],
            "reviewer_b_outcome": b["outcome"], "reviewer_b_rationale": b["rationale"],
        })
    return review_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase4", type=Path, default=ROOT / "experiments" / "phase4")
    parser.add_argument("--package", type=Path, default=ROOT / "experiments" / "phase5" / "restricted_annotation_v2")
    parser.add_argument("--reviewer-a", type=Path, required=True)
    parser.add_argument("--reviewer-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(**vars(args)), sort_keys=True))
