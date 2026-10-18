"""Create an immutable source/provenance manifest separate from run inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

if __package__:
    from scripts.inspect_phase4_jbb import ROOT, audit
    from scripts.prepare_phase4_jbb_pilot import INDICES, OUT, _write_once
else:
    from inspect_phase4_jbb import ROOT, audit
    from prepare_phase4_jbb_pilot import INDICES, OUT, _write_once


def build() -> dict[str, object]:
    source_audit = audit()
    source_path = OUT / "jbb_pilot_dataset_v1.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if tuple(source["selection"]["indices"]) != INDICES:
        raise ValueError("selected source IDs differ from frozen pilot selection")
    manifest = {
        "manifest_version": "phase4-jbb-source-manifest-v1",
        "research_status": "real_source_exploratory_pilot_not_confirmatory",
        "dataset_id": source["dataset_id"], "dataset_version": source["dataset_version"],
        "source_revisions": source["source_revisions"],
        "source_files_sha256": source_audit["source_hashes"],
        "dataset_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "source_urls": {
            "behaviors": "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors",
            "attack_artifacts": "https://github.com/JailbreakBench/artifacts",
        },
        "license": {"behaviors": "MIT; local LICENSE in pinned behavior directory",
                    "attack_artifacts": "MIT; local LICENSE in pinned artifact directory",
                    "constituent_sources": "Source field retained; constituent-citation review still required"},
        "source_counts": {"harmful": source_audit["harmful_rows"],
                          "benign": source_audit["benign_rows"],
                          "three_verified_artifact_methods": len(source_audit["artifact_complete_matching_indices"])},
        "selected_case_ids": [f"jbb-{index}" for index in INDICES],
        "selected_categories": [row["category"] for row in source["lineage"] if "source_index" in row],
        "historical_calibration_exact_overlap_count_all_harmful": source_audit["historical_calibration_goal_overlap_count"],
        "historical_calibration_lexical_near_overlap_count_all_harmful": source_audit["historical_calibration_near_overlap_count"],
        "selected_calibration_overlap": False,
        "harmful_internal_lexical_near_duplicate_pairs": source_audit["harmful_goal_lexical_near_duplicate_pairs"],
        "related_group_ids": [f"jbb-goal-{index}" for index in INDICES],
        "split": "exploratory_pilot_only; no development/validation/held-out claim",
        "attack_lineage": source["lineage"],
        "source_fields_not_present": ["human label for new target response", "sequential attack design",
                                      "validated benign semantic match", "model-independent attack efficacy"],
        "handling": "Treat raw goals, attack prompts, responses, blinded batches and private join map as restricted research data; no public response release without review.",
    }
    path = OUT / "jbb_research_manifest_v1.json"
    return {"manifest_sha256": _write_once(path, manifest),
            "selected_cases": manifest["selected_case_ids"],
            "source_complete_methods": manifest["source_counts"]["three_verified_artifact_methods"]}


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
