"""Prepare a source-pinned, exploratory JBB pilot without outcome labels."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

if __package__:
    from scripts.inspect_phase4_jbb import ARTIFACTS, BEHAVIORS, CALIBRATION, ROOT, audit
else:
    from inspect_phase4_jbb import ARTIFACTS, BEHAVIORS, CALIBRATION, ROOT, audit

OUT = ROOT / "experiments" / "phase4"
INDICES = ("1", "51")  # Selected by category/coverage and calibration separation before any local target response.
METHODS = (
    ("PAIR", "PAIR-black_box-vicuna-13b-v1.5.json", "vicuna-13b-v1.5"),
    ("GCG", "GCG-transfer-gpt-3.5-turbo-1106.json", "gpt-3.5-turbo-1106"),
    ("JBC", "JBC-manual-vicuna-13b-v1.5.json", "vicuna-13b-v1.5"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["Index"]: row for row in csv.DictReader(handle)}


def _write_once(path: Path, payload: dict[str, object]) -> str:
    encoded = (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise FileExistsError(f"immutable pilot artifact differs: {path}")
    else:
        with path.open("xb") as handle:
            handle.write(encoded)
    return _sha(path)


def prepare() -> dict[str, object]:
    source_audit = audit()
    eligible = {row["index"] for row in source_audit["artifact_complete_matching_indices"]}
    if not set(INDICES) <= eligible:
        raise ValueError("selected indices lack three verified source attack prompts")
    overlap = set(source_audit["historical_calibration_goal_overlap_indices"])
    if set(INDICES) & overlap:
        raise ValueError("selected pilot goals overlap historical calibration goals")
    harmful = _rows(BEHAVIORS / "harmful-behaviors.csv")
    benign = _rows(BEHAVIORS / "benign-behaviors.csv")
    artifact_rows = {name: {str(row["index"]): row for row in
                     json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))["jailbreaks"]}
                     for _, name, _ in METHODS}
    calibration = list(csv.DictReader(CALIBRATION.open(encoding="utf-8-sig", newline="")))
    calibration_goals = [" ".join(row["goal"].casefold().split()) for row in calibration]
    cases, lineage = [], []
    for index in INDICES:
        h, b = harmful[index], benign[index]
        if h["Category"] != b["Category"]:
            raise ValueError("same-index benign category does not match harmful category")
        normalized_goal = " ".join(h["Goal"].casefold().split())
        max_similarity = max((SequenceMatcher(None, normalized_goal, goal).ratio()
                              for goal in calibration_goals), default=0.0)
        if max_similarity >= 0.9:
            raise ValueError("selected goal is lexically near a historical calibration goal")
        attacks = []
        for method, filename, prior_target in METHODS:
            artifact = artifact_rows[filename][index]
            if artifact["goal"].strip() != h["Goal"].strip() or artifact["category"] != h["Category"]:
                raise ValueError("source attack and behavior metadata disagree")
            if not artifact["prompt"].strip():
                raise ValueError("source attack prompt missing")
            attacks.append({"attack_id": f"jbb-{method.lower()}-{index}",
                            "attack_instance_id": f"jbb-{index}-{method.lower()}",
                            "attack_family": method, "prompt": artifact["prompt"]})
            lineage.append({"case_id": f"jbb-{index}", "attack_family": method,
                            "artifact_file": str((ARTIFACTS / filename).relative_to(ROOT)),
                            "artifact_sha256": _sha(ARTIFACTS / filename),
                            "prior_target_model": prior_target,
                            "prompt_sha256": hashlib.sha256(artifact["prompt"].encode("utf-8")).hexdigest()})
        sequence = [item["attack_instance_id"] for item in attacks]
        cases.append({"evaluation_case_id": f"jbb-{index}",
                      "baseline_prompt": h["Goal"], "attacks": attacks,
                      "sequences": [sequence, list(reversed(sequence))],
                      "recovery_probes": [h["Goal"], h["Goal"]],
                      "benign_control_prompts": [b["Goal"]] * 3,
                      "benign_recovery_probes": [b["Goal"]] * 2})
        lineage.append({"case_id": f"jbb-{index}", "source_index": index,
                        "category": h["Category"], "source": h["Source"],
                        "harmful_goal_sha256": hashlib.sha256(h["Goal"].encode("utf-8")).hexdigest(),
                        "benign_goal_sha256": hashlib.sha256(b["Goal"].encode("utf-8")).hexdigest(),
                        "benign_match": "same source index and category; semantic/length match not validated",
                        "max_calibration_goal_lexical_similarity": max_similarity})
    OUT.mkdir(parents=True, exist_ok=True)
    dataset = {"dataset_id": "jbb-phase4-exploratory-subset", "dataset_version": "behaviors-886acc3-artifacts-909e68c-v1",
               "cases": cases,
               "source_revisions": {"behaviors": source_audit["dataset_revision"],
                                    "attack_artifacts": source_audit["artifact_revision"]},
               "license": "MIT source repositories; preserve upstream notices and constituent citations",
               "selection": {"indices": list(INDICES), "rule": "preselected same-index harmful/benign category pair, complete three-artifact alignment, no exact or lexical-near calibration goal overlap; independent of local target outcomes"},
               "split": "exploratory_pilot_only_no_held_out_claim",
               "lineage": lineage}
    dataset_path = OUT / "jbb_pilot_dataset_v1.json"
    dataset_hash = _write_once(dataset_path, dataset)
    spec = {
        "experiment_id": "phase4-jbb-exploratory-pilot-v1", "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["dataset_version"], "dataset_hash": dataset_hash,
        "cases": cases,
        "models": [
            {"name": "qwen3.5:2b", "provider": "ollama-local",
             "version": "324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df",
             "context_window": 8192, "capabilities": ["thinking"]},
            {"name": "gemma3:4b", "provider": "ollama-local",
             "version": "a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a",
             "context_window": 8192, "capabilities": []},
        ],
        "generation": {"temperature": 0.0, "max_new_tokens": 96, "timeout_seconds": 90},
        "seeds": [2026], "repetitions": 1,
        "measurement": {"behavior_representation_version": "unvalidated_phase4_pilot",
                        "layer1_version": None, "layer2_judge_version": None,
                        "prompt_version": "jbb-sourced-phase4-v1", "rubric_version": "phase4-outcome-rubric-draft-v1",
                        "measurement_version": "unvalidated_phase4_pilot",
                        "threat_model": "jbb_harmful_behavior_attack"},
        "preregistration_id": "phase4-local-exploratory-lock-v1",
        "metadata": {"evidence_class": "exploratory", "scientific_eligibility": False,
                     "human_labels": "none", "split": dataset["split"]},
        "canary_policy": {"enabled": False},
    }
    specification_path = OUT / "jbb_pilot_specification_v1.json"
    specification_hash = _write_once(specification_path, spec)
    lock_path = OUT / "jbb_pilot_local_lock_v1.json"
    lock = {"protocol_id": "phase4-local-exploratory-lock-v1",
            "preregistration_id": spec["preregistration_id"], "experiment_id": spec["experiment_id"],
            "status": "locally_frozen", "external_registration": False,
            "evidence_class": "exploratory", "dataset_sha256": dataset_hash,
            "specification_sha256": specification_hash,
            "locked_at": datetime.now(timezone.utc).isoformat(),
            "amendment_policy": "append a new version with reason; never overwrite this lock"}
    if lock_path.exists():
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
        if any(existing.get(key) != lock[key] for key in
               ("protocol_id", "experiment_id", "status", "dataset_sha256", "specification_sha256")):
            raise FileExistsError("existing pilot lock differs; create amendment")
    else:
        _write_once(lock_path, lock)
    return {"dataset_sha256": dataset_hash, "specification_sha256": specification_hash,
            "local_lock_sha256": _sha(lock_path), "case_count": len(cases),
            "planned_calls": 25 * len(cases) * len(spec["models"])}


if __name__ == "__main__":
    print(json.dumps(prepare(), sort_keys=True))
