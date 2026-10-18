"""Build human-review candidates from completed immutable experiment observations.

Task and attack objectives are researcher supplied; they are never inferred from
the target's response or from detector output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping


def candidates_from_observations(observation_dir: Path, objectives: Mapping[str, object],
                                 *, experiment_id: str) -> dict[str, object]:
    cases = objectives.get("cases")
    if not isinstance(cases, dict) or not experiment_id:
        raise ValueError("versioned case objectives and experiment ID are required")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for path in sorted(observation_dir.glob("*.json")):
        raw = path.read_bytes()
        observation = json.loads(raw)
        if observation.get("experiment_id") != experiment_id:
            raise ValueError(f"observation belongs to another experiment: {path.name}")
        if observation.get("condition") not in ("isolated_attack", "sequential_attack"):
            continue
        if observation.get("status") != "completed" or not isinstance(observation.get("response"), str) or not observation["response"].strip():
            continue
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or path.stem != observation_id or observation_id in seen:
            raise ValueError(f"observation identity is invalid: {path.name}")
        seen.add(observation_id)
        case_id = observation.get("evaluation_case_id")
        attack_id = observation.get("attack_instance_id")
        design = cases.get(case_id)
        if not isinstance(design, dict) or not isinstance(design.get("attacks"), dict):
            raise ValueError(f"no predeclared objective for case {case_id}")
        legitimate_task = design.get("legitimate_task")
        adversarial_objective = design["attacks"].get(attack_id)
        if not isinstance(legitimate_task, str) or not legitimate_task.strip() or not isinstance(adversarial_objective, str) or not adversarial_objective.strip():
            raise ValueError(f"missing predeclared task or attack objective: {case_id}/{attack_id}")
        family = observation.get("attack_family")
        history = observation.get("ordered_messages")
        if not isinstance(family, str) or not family or not isinstance(history, list):
            raise ValueError(f"observation lacks attack family or conversation history: {observation_id}")
        rows.append({"evaluation_id": observation_id, "legitimate_task": legitimate_task,
                     "adversarial_objective": adversarial_objective,
                     "target_response": observation["response"],
                     "conversation_history": history, "attack_family": family,
                     "source_artifact": str(path.resolve()),
                     "source_sha256": hashlib.sha256(raw).hexdigest()})
    if not rows:
        raise ValueError("no completed attack observations available for annotation")
    return {"schema_version": "annotation-candidates-v1", "experiment_id": experiment_id,
            "objectives_version": objectives.get("version"), "candidates": rows}
