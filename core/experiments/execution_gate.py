"""Pre-execution checks for bounded, source-pinned controlled experiments."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from core.experiments.models import ExperimentSpecification


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def planned_calls(spec: ExperimentSpecification) -> int:
    per_repetition = 0
    for case in spec.cases:
        per_repetition += 1 + 2 * len(case.attacks)
        per_repetition += sum(1 + len(sequence) + len(case.recovery_probes)
                              for sequence in case.sequences)
        if case.benign_control_prompts:
            per_repetition += 1 + len(case.benign_control_prompts) + len(case.benign_recovery_probes)
    return per_repetition * len(spec.models) * spec.repetitions


def verify_dataset_source(spec: ExperimentSpecification, source: Path) -> str:
    digest = sha256_file(source)
    if digest != spec.dataset_hash:
        raise ValueError("dataset_source_hash_mismatch")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("dataset_id") != spec.dataset_id or payload.get("dataset_version") != spec.dataset_version:
        raise ValueError("dataset_source_identity_mismatch")
    source_cases = payload.get("cases")
    if not isinstance(source_cases, list) or not source_cases:
        raise ValueError("dataset_source_has_no_cases")
    ids = [case.get("evaluation_case_id") for case in source_cases]
    if len(set(ids)) != len(ids) or any(not case_id for case_id in ids):
        raise ValueError("dataset_source_case_ids_invalid")
    expected = json.loads(json.dumps([asdict(case) for case in spec.cases]))
    for case in source_cases:
        case.setdefault("recovery_probes", [])
        case.setdefault("benign_control_prompts", [])
        case.setdefault("benign_recovery_probes", [])
    if source_cases != expected:
        raise ValueError("dataset_source_case_content_mismatch")
    return digest


def verify_local_protocol(spec: ExperimentSpecification, specification_path: Path,
                          protocol_path: Path) -> dict[str, object]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("status") != "locally_frozen":
        raise ValueError("protocol_not_locally_frozen")
    if protocol.get("experiment_id") != spec.experiment_id:
        raise ValueError("protocol_experiment_mismatch")
    if protocol.get("specification_sha256") != sha256_file(specification_path):
        raise ValueError("protocol_specification_hash_mismatch")
    if protocol.get("dataset_sha256") != spec.dataset_hash:
        raise ValueError("protocol_dataset_hash_mismatch")
    if protocol.get("preregistration_id") != spec.preregistration_id:
        raise ValueError("protocol_preregistration_mismatch")
    return protocol
