"""Blinded human annotation transport with explicit independent/adjudicated labels.

No function in this module generates a human judgment or infers one from text.
The rater-facing export never contains the source evaluation ID or model name.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Mapping, Sequence

from core.evaluation.attack_outcome import AttackOutcomeRecord, AttackOutcomeStatus
from core.experiments.persistence import append_scientific_artifact

OUTCOMES = frozenset({"success", "failure", "partial", "ambiguous", "unavailable"})


def create_annotation_batch(candidates: Sequence[Mapping[str, object]], *, batch_id: str,
                            rubric_version: str, salt: str, shuffle_seed: int) -> tuple[dict, dict]:
    """Return separate rater-facing and private join-map documents."""
    if not batch_id or not rubric_version or len(salt) < 16 or not candidates:
        raise ValueError("batch, rubric, high-entropy salt, and candidates are required")
    items, mapping = [], {}
    source_ids = set()
    for row in candidates:
        source_id = _required_text(row, "evaluation_id")
        if source_id in source_ids:
            raise ValueError("duplicate source evaluation")
        source_ids.add(source_id)
        sample_id = hashlib.sha256(f"{salt}:{batch_id}:{source_id}".encode()).hexdigest()[:24]
        history = row.get("conversation_history", [])
        if not isinstance(history, list) or not all(isinstance(item, dict) for item in history):
            raise ValueError("conversation_history must be a list of message objects")
        history = [{"role": _required_text(item, "role"), "content": _required_text(item, "content")}
                   for item in history]
        fixture = row.get("synthetic_fixture") is True
        source_sha256 = _required_text(row, "source_sha256")
        if not fixture and re.fullmatch(r"[0-9a-fA-F]{64}", source_sha256) is None:
            raise ValueError("real source_sha256 must be a 64-character hex digest")
        item = {"sample_id": sample_id,
                "legitimate_task": _required_text(row, "legitimate_task"),
                "adversarial_objective": _required_text(row, "adversarial_objective"),
                "target_response": _required_text(row, "target_response"),
                "conversation_history": history}
        items.append(item)
        mapping[sample_id] = {"evaluation_id": source_id,
                              "attack_family": _required_text(row, "attack_family"),
                              "source_artifact": _required_text(row, "source_artifact"),
                              "source_sha256": source_sha256, "synthetic_fixture": fixture}
    random.Random(shuffle_seed).shuffle(items)
    public = {"schema_version": "human-annotation-v1", "batch_id": batch_id,
              "rubric_version": rubric_version, "items": items,
              "notice": "Human raters must independently apply the cited rubric; confidence is not a calibrated probability."}
    private = {"schema_version": "human-annotation-map-v1", "batch_id": batch_id,
               "rubric_version": rubric_version, "mapping": mapping}
    return public, private


def validate_annotation_import(public: Mapping[str, object], private: Mapping[str, object],
                               judgments: Sequence[Mapping[str, object]],
                               adjudications: Sequence[Mapping[str, object]], *,
                               label_version: str) -> dict[str, object]:
    """Require two independent humans; disagreement needs an explicit adjudicator."""
    if not label_version or public.get("schema_version") != "human-annotation-v1" or private.get("schema_version") != "human-annotation-map-v1":
        raise ValueError("annotation schema or label version is invalid")
    if public.get("batch_id") != private.get("batch_id") or public.get("rubric_version") != private.get("rubric_version"):
        raise ValueError("public batch and private map identity differ")
    items = public.get("items")
    mapping = private.get("mapping")
    if not isinstance(items, list) or not isinstance(mapping, dict) or not items:
        raise ValueError("annotation batch is empty or invalid")
    sample_ids = {item.get("sample_id") for item in items if isinstance(item, dict)}
    if (len(sample_ids) != len(items) or sample_ids != set(mapping)
            or any(not isinstance(sample_id, str) or not sample_id for sample_id in sample_ids)):
        raise ValueError("annotation sample IDs and private map differ")
    source_ids = set()
    for sample_id in sample_ids:
        source = mapping[sample_id]
        if not isinstance(source, dict):
            raise ValueError("private map entry must be an object")
        evaluation_id = _required_text(source, "evaluation_id")
        _required_text(source, "attack_family")
        _required_text(source, "source_artifact")
        digest = _required_text(source, "source_sha256")
        if source.get("synthetic_fixture") is not True and re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
            raise ValueError("real source_sha256 must be a 64-character hex digest")
        if source.get("synthetic_fixture") is not True:
            artifact_path = Path(source["source_artifact"])
            if not artifact_path.is_file() or hashlib.sha256(artifact_path.read_bytes()).hexdigest() != digest.lower():
                raise ValueError("source artifact is missing or changed since annotation export")
        if evaluation_id in source_ids:
            raise ValueError("duplicate source evaluation in private map")
        source_ids.add(evaluation_id)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in judgments:
        sample_id = _required_text(row, "sample_id")
        rater_id = _required_text(row, "rater_id")
        outcome = _outcome(row)
        if sample_id not in sample_ids or any(item["rater_id"] == rater_id for item in grouped[sample_id]):
            raise ValueError("unknown sample or duplicate rater judgment")
        grouped[sample_id].append({"sample_id": sample_id, "rater_id": rater_id,
                                   "outcome": outcome, "rationale": _required_text(row, "rationale")})
    decisions: dict[str, dict] = {}
    for row in adjudications:
        sample_id = _required_text(row, "sample_id")
        if sample_id not in sample_ids or sample_id in decisions:
            raise ValueError("unknown or duplicate adjudication")
        decisions[sample_id] = {"sample_id": sample_id,
                                "adjudicator_id": _required_text(row, "adjudicator_id"),
                                "outcome": _outcome(row), "rationale": _required_text(row, "rationale")}
    final = []
    disagreements = 0
    for sample_id in sorted(sample_ids):
        labels = grouped[sample_id]
        if len(labels) < 2:
            raise ValueError(f"at least two independent judgments required for {sample_id}")
        if sample_id in decisions and decisions[sample_id]["adjudicator_id"] in {item["rater_id"] for item in labels}:
            raise ValueError("adjudicator must be independent of the original raters")
        distinct = {item["outcome"] for item in labels}
        if len(distinct) == 1 and sample_id in decisions:
            raise ValueError(f"adjudication without disagreement is not allowed for {sample_id}")
        if len(distinct) > 1:
            disagreements += 1
            if sample_id not in decisions:
                raise ValueError(f"disagreement requires adjudication for {sample_id}")
        outcome = decisions[sample_id]["outcome"] if sample_id in decisions else labels[0]["outcome"]
        final.append({"sample_id": sample_id, "evaluation_id": mapping[sample_id]["evaluation_id"],
                      "attack_family": mapping[sample_id]["attack_family"], "outcome": outcome,
                      "label_source": "human_adjudication" if sample_id in decisions else "independent_human_agreement"})
    return {"batch_id": public["batch_id"], "rubric_version": public["rubric_version"],
            "label_version": label_version, "judgments": tuple(item for labels in grouped.values() for item in labels),
            "adjudications": tuple(decisions.values()), "final": tuple(final),
            "disagreements": disagreements, "sample_count": len(items)}


def persist_annotation_import(session, validated: Mapping[str, object], private: Mapping[str, object], *,
                              extra_provenance: Mapping[str, object] | None = None) -> None:
    """Append individual judgments, adjudications, and derived outcome contracts."""
    batch_id = str(validated["batch_id"])
    label_version = str(validated["label_version"])
    mapping = private["mapping"]
    for judgment in validated["judgments"]:
        sample_id = judgment["sample_id"]
        source = mapping[sample_id]
        append_scientific_artifact(session, record_id=f"human:{batch_id}:{sample_id}:{judgment['rater_id']}",
            family="human_annotation", schema_version="human-annotation-v1", scope="evaluation",
            owner_id=source["evaluation_id"], status="independent", artifact=judgment,
            provenance=_label_provenance(validated, source, extra_provenance), commit=False)
    for decision in validated["adjudications"]:
        sample_id = decision["sample_id"]
        source = mapping[sample_id]
        append_scientific_artifact(session, record_id=f"adjudication:{batch_id}:{sample_id}",
            family="human_adjudication", schema_version="human-annotation-v1", scope="evaluation",
            owner_id=source["evaluation_id"], status="adjudicated", artifact=decision,
            provenance=_label_provenance(validated, source, extra_provenance), commit=False)
    for item in validated["final"]:
        source = mapping[item["sample_id"]]
        classified = item["outcome"] in {"success", "failure"}
        status = AttackOutcomeStatus.CLASSIFIED if classified else AttackOutcomeStatus(item["outcome"] if item["outcome"] in {"ambiguous", "unavailable"} else "ambiguous")
        outcome = AttackOutcomeRecord(
            evaluation_id=item["evaluation_id"], attack_family=item["attack_family"],
            evaluator_id=item["label_source"], evaluator_version=label_version,
            success=item["outcome"] == "success" if classified else None, status=status,
            reason=None if classified else item["outcome"],
            evidence={"batch_id": batch_id, "sample_id": item["sample_id"]},
            provenance=_label_provenance(validated, source, extra_provenance), label_source=item["label_source"],
            label_version=label_version)
        append_scientific_artifact(session,
            record_id=f"human-outcome:{label_version}:{item['evaluation_id']}", family="attack_outcome",
            schema_version=outcome.outcome_version, scope="evaluation", owner_id=item["evaluation_id"],
            status=status.value, artifact=outcome, provenance=_label_provenance(validated, source, extra_provenance), commit=False)
    session.commit()


def _label_provenance(validated, source, extra_provenance=None):
    return {"batch_id": validated["batch_id"], "rubric_version": validated["rubric_version"],
            "label_version": validated["label_version"], "source_artifact": source["source_artifact"],
            "source_sha256": source["source_sha256"],
            "data_origin": "synthetic_fixture" if source.get("synthetic_fixture") else "human_annotation",
            "fixture": bool(source.get("synthetic_fixture")),
            "scientifically_validated": False, **dict(extra_provenance or {})}


def _required_text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be nonempty text")
    return value.strip()


def _outcome(row: Mapping[str, object]) -> str:
    value = _required_text(row, "outcome")
    if value not in OUTCOMES:
        raise ValueError("unsupported annotation outcome")
    return value
