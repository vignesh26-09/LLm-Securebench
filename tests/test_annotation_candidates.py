"""Synthetic, real-shaped fixtures for the immutable observation export gate."""

import hashlib
import json

import pytest

from core.evaluation.annotation_candidates import candidates_from_observations


def _observation(root, **changes):
    value = {"observation_id": "obs-1", "experiment_id": "exp-1",
             "condition": "isolated_attack", "status": "completed",
             "evaluation_case_id": "case-1", "attack_instance_id": "attack-1",
             "attack_family": "synthetic-family", "response": "synthetic response",
             "ordered_messages": [{"role": "user", "content": "synthetic prompt"}]}
    value.update(changes)
    path = root / "obs-1.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _objectives():
    return {"version": "synthetic-v1", "cases": {"case-1": {
        "legitimate_task": "Synthetic legitimate task",
        "attacks": {"attack-1": "Synthetic adversarial objective"}}}}


def test_candidates_are_sourced_and_hashed(tmp_path):
    path = _observation(tmp_path)
    result = candidates_from_observations(tmp_path, _objectives(), experiment_id="exp-1")
    candidate = result["candidates"][0]
    assert candidate["evaluation_id"] == "obs-1"
    assert candidate["source_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert candidate["target_response"] == "synthetic response"
    assert candidate["adversarial_objective"] == "Synthetic adversarial objective"


def test_candidates_reject_missing_predeclared_objective(tmp_path):
    _observation(tmp_path)
    with pytest.raises(ValueError, match="no predeclared objective"):
        candidates_from_observations(tmp_path, {"cases": {}}, experiment_id="exp-1")


def test_candidates_never_export_failed_response_as_successful_observation(tmp_path):
    _observation(tmp_path, status="failed")
    with pytest.raises(ValueError, match="no completed attack observations"):
        candidates_from_observations(tmp_path, _objectives(), experiment_id="exp-1")
