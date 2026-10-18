"""Audit real annotation transport and prepare blank independent review forms.

This module never predicts, assigns, or imports an outcome label.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence

REQUIRED_OBSERVATION_FIELDS = (
    "observation_id", "experiment_id", "evaluation_case_id", "attack_instance_id",
    "attack_family", "target_model", "target_model_version", "provider",
    "generation_configuration", "timestamp", "ordered_messages", "response",
    "condition", "status", "context_status", "dataset_version",
)
PUBLIC_FIELDS = frozenset({"sample_id", "legitimate_task", "adversarial_objective",
                           "conversation_history", "target_response"})
FORM_FIELDS = ("sample_id", "legitimate_task", "adversarial_objective",
               "context_before_response", "target_response", "rater_id", "outcome", "rationale")


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_annotation_batch(*, observations_dir: Path, objectives_path: Path,
                           candidates_path: Path, public_path: Path,
                           private_path: Path) -> dict[str, object]:
    """Require a one-to-one, content-exact path from saved attack calls to samples."""
    objectives, candidates = _read(objectives_path), _read(candidates_path)
    public, private = _read(public_path), _read(private_path)
    phase4 = observations_dir.parent.parent
    manifest = _read(observations_dir.parent / "manifest.json")
    dataset_path = phase4 / "jbb_pilot_dataset_v1.json"
    specification_path = phase4 / "jbb_pilot_specification_v1.json"
    lock = _read(phase4 / "jbb_pilot_local_lock_v1.json")
    specification = _read(specification_path)
    artifact_hashes = manifest.get("artifact_hashes")
    files = sorted(observations_dir.glob("*.json"))
    if (not isinstance(artifact_hashes, dict) or len(artifact_hashes) != len(files)
            or manifest.get("successful_count") != len(files)
            or manifest.get("failed_count") != 0
            or manifest.get("experiment_id") != candidates.get("experiment_id")
            or manifest.get("dataset_identity", {}).get("hash") != _sha(dataset_path)
            or objectives.get("source_dataset_sha256") != _sha(dataset_path)
            or specification.get("dataset_hash") != _sha(dataset_path)
            or lock.get("dataset_sha256") != _sha(dataset_path)
            or lock.get("specification_sha256") != _sha(specification_path)):
        raise ValueError("run manifest, dataset, specification, or local lock differs")
    for path in files:
        relative = str(path.relative_to(observations_dir.parent))
        if artifact_hashes.get(relative) != _sha(path):
            raise ValueError(f"saved observation differs from run manifest: {path.name}")
    if (candidates.get("objectives_version") != objectives.get("version")
            or public.get("schema_version") != "human-annotation-v1"
            or private.get("schema_version") != "human-annotation-map-v1"
            or public.get("batch_id") != private.get("batch_id")
            or public.get("rubric_version") != private.get("rubric_version")):
        raise ValueError("annotation source, batch, or rubric versions differ")
    cases = objectives.get("cases")
    rows, items, mapping = candidates.get("candidates"), public.get("items"), private.get("mapping")
    if not isinstance(cases, dict) or not isinstance(rows, list) or not isinstance(items, list) or not isinstance(mapping, dict):
        raise ValueError("annotation objectives/candidates/batch schema is incomplete")
    attack_files = {}
    for path in files:
        observation = _read(path)
        if (observation.get("condition") in {"isolated_attack", "sequential_attack"}
                and observation.get("status") == "completed"):
            attack_files[path.stem] = path
    if not attack_files or len(rows) != len(items) or len(rows) != len(mapping) or len(rows) != len(attack_files):
        raise ValueError("completed attack observations and exported sample counts differ")
    by_evaluation = {}
    content_fingerprints = Counter()
    missing_context = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("annotation candidate is not an object")
        evaluation_id = row.get("evaluation_id")
        if evaluation_id in by_evaluation or evaluation_id not in attack_files:
            raise ValueError("duplicate, unknown, or missing candidate evaluation ID")
        path = attack_files[evaluation_id]
        observation = _read(path)
        if any(observation.get(field) in (None, "", [], {}) for field in REQUIRED_OBSERVATION_FIELDS):
            raise ValueError(f"incomplete observation provenance: {evaluation_id}")
        if observation["observation_id"] != evaluation_id or observation["experiment_id"] != candidates.get("experiment_id"):
            raise ValueError(f"observation identity mismatch: {evaluation_id}")
        design = cases.get(observation["evaluation_case_id"])
        if not isinstance(design, dict) or not isinstance(design.get("attacks"), dict):
            raise ValueError(f"case objective missing: {evaluation_id}")
        expected_objective = design["attacks"].get(observation["attack_instance_id"])
        if not isinstance(expected_objective, str) or not expected_objective.strip():
            raise ValueError(f"attack objective missing: {evaluation_id}")
        history = observation["ordered_messages"]
        if not isinstance(history, list) or not history or any(
                not isinstance(message, dict) or message.get("role") not in {"system", "user", "assistant"}
                or not isinstance(message.get("content"), str) or not message["content"].strip()
                for message in history):
            missing_context += 1
            raise ValueError(f"conversation history incomplete: {evaluation_id}")
        if history[-1]["role"] != "assistant" or history[-1]["content"] != observation["response"]:
            raise ValueError(f"saved target response is not terminal message: {evaluation_id}")
        if (row.get("target_response") != observation["response"]
                or row.get("conversation_history") != history
                or row.get("attack_family") != observation["attack_family"]
                or row.get("legitimate_task") != design.get("legitimate_task")
                or row.get("adversarial_objective") != expected_objective
                or Path(str(row.get("source_artifact", ""))).resolve() != path.resolve()
                or row.get("source_sha256") != _sha(path)):
            raise ValueError(f"candidate differs from persisted source/objective: {evaluation_id}")
        by_evaluation[evaluation_id] = row
        fingerprint = hashlib.sha256(json.dumps(
            [expected_objective, history, observation["response"]],
            sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        content_fingerprints[fingerprint] += 1
    if set(by_evaluation) != set(attack_files):
        raise ValueError("candidate export omits a completed attack observation")
    public_ids = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != PUBLIC_FIELDS:
            raise ValueError("public item contains missing or unblinded fields")
        sample_id = item.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id or sample_id in public_ids or sample_id not in mapping:
            raise ValueError("duplicate or unknown public sample ID")
        public_ids.add(sample_id)
        source = mapping[sample_id]
        if not isinstance(source, dict) or source.get("synthetic_fixture") is not False:
            raise ValueError("real batch maps to invalid or fixture source")
        evaluation_id = source.get("evaluation_id")
        if evaluation_id not in by_evaluation:
            raise ValueError("private map has unknown source evaluation")
        row = by_evaluation[evaluation_id]
        expected_history = [{"role": message["role"], "content": message["content"]}
                            for message in row["conversation_history"]]
        if (source.get("source_artifact") != row["source_artifact"]
                or source.get("source_sha256") != row["source_sha256"]
                or source.get("attack_family") != row["attack_family"]
                or item["legitimate_task"] != row["legitimate_task"]
                or item["adversarial_objective"] != row["adversarial_objective"]
                or item["target_response"] != row["target_response"]
                or item["conversation_history"] != expected_history):
            raise ValueError(f"blinded item or private map differs from source: {sample_id}")
    if public_ids != set(mapping) or len({entry["evaluation_id"] for entry in mapping.values()}) != len(mapping):
        raise ValueError("public/private sample mapping is incomplete or duplicated")
    return {
        "status": "source_verified_reviewer_ready_unlabeled",
        "completed_attack_observations": len(attack_files),
        "candidate_count": len(rows), "blinded_sample_count": len(items),
        "duplicate_evaluation_ids": 0, "duplicate_sample_ids": 0,
        "duplicate_exact_content_groups": sum(count > 1 for count in content_fingerprints.values()),
        "missing_context_count": missing_context, "missing_objective_count": 0,
        "source_hash_mismatches": 0, "human_label_count": 0,
        "batch_id": public["batch_id"], "rubric_version": public["rubric_version"],
        "objectives_sha256": _sha(objectives_path), "candidates_sha256": _sha(candidates_path),
        "public_sha256": _sha(public_path), "private_map_sha256": _sha(private_path),
    }


def form_csv(public: Mapping[str, object]) -> bytes:
    """Full context for one independent reviewer, with blank judgment fields."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FORM_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in public["items"]:
        history = item["conversation_history"]
        context = history[:-1] if history and history[-1] == {
            "role": "assistant", "content": item["target_response"]} else history
        writer.writerow({
            "sample_id": item["sample_id"],
            "legitimate_task": item["legitimate_task"],
            "adversarial_objective": item["adversarial_objective"],
            "context_before_response": json.dumps(context, ensure_ascii=False),
            "target_response": item["target_response"],
            "rater_id": "", "outcome": "", "rationale": "",
        })
    return output.getvalue().encode("utf-8-sig")


def judgments_from_forms(public: Mapping[str, object], reviewer_a: Path,
                         reviewer_b: Path) -> list[dict[str, str]]:
    """Require two complete independent forms with unchanged blinded evidence."""
    template = list(csv.DictReader(io.StringIO(form_csv(public).decode("utf-8-sig"))))
    expected = {row["sample_id"]: row for row in template}
    all_judgments = []
    reviewer_ids = []
    for path in (reviewer_a, reviewer_b):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != FORM_FIELDS:
                raise ValueError("reviewer form columns differ from versioned template")
            rows = list(reader)
        if len(rows) != len(expected) or len({row["sample_id"] for row in rows}) != len(expected):
            raise ValueError("reviewer form has missing or duplicate samples")
        rater_ids = {row["rater_id"].strip() for row in rows}
        if len(rater_ids) != 1 or not next(iter(rater_ids)):
            raise ValueError("reviewer must use one nonempty pseudonymous rater ID")
        reviewer_ids.append(next(iter(rater_ids)))
        for row in rows:
            sample_id = row["sample_id"]
            if sample_id not in expected or any(row[field] != expected[sample_id][field]
                                                for field in FORM_FIELDS[:5]):
                raise ValueError("reviewer form changes source context or sample ID")
            if row["outcome"] not in {"success", "failure", "partial", "ambiguous", "unavailable"}:
                raise ValueError("reviewer outcome is blank or unsupported")
            if not row["rationale"].strip():
                raise ValueError("reviewer rationale is required")
            all_judgments.append({"sample_id": sample_id, "rater_id": row["rater_id"].strip(),
                                  "outcome": row["outcome"], "rationale": row["rationale"].strip()})
    if reviewer_ids[0] == reviewer_ids[1]:
        raise ValueError("the two reviewer forms must have independent rater IDs")
    return all_judgments


def adjudications_from_form(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != ("sample_id", "adjudicator_id", "outcome", "rationale"):
            raise ValueError("adjudication form columns are invalid")
        return [{key: str(value).strip() for key, value in row.items()} for row in reader]


def independent_agreement(judgments: Sequence[Mapping[str, str]]) -> dict[str, object]:
    """Five-category raw agreement and Cohen's kappa before adjudication."""
    pairs: dict[str, list[str]] = {}
    for row in judgments:
        pairs.setdefault(row["sample_id"], []).append(row["outcome"])
    if not pairs or any(len(pair) != 2 for pair in pairs.values()):
        raise ValueError("agreement requires exactly two judgments per sample")
    n = len(pairs)
    labels = ("success", "failure", "partial", "ambiguous", "unavailable")
    first = Counter(pair[0] for pair in pairs.values())
    second = Counter(pair[1] for pair in pairs.values())
    observed = sum(pair[0] == pair[1] for pair in pairs.values()) / n
    expected = sum(first[label] * second[label] for label in labels) / (n * n)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    return {"sample_count": n, "agreement": observed, "cohen_kappa": kappa,
            "disagreements": sum(pair[0] != pair[1] for pair in pairs.values()),
            "label_order": list(labels),
            "confusion_matrix": {a: {b: sum(pair == [a, b] for pair in pairs.values())
                                     for b in labels} for a in labels}}
