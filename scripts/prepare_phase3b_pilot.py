"""Create one immutable, harmless engineering-pilot specification and local lock."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "experiments" / "phase3b"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> dict[str, str]:
    source = PILOT / "pilot_dataset_v1.json"
    specification = PILOT / "pilot_specification_v1.json"
    lock = PILOT / "pilot_protocol_lock_v1.json"
    dataset = json.loads(source.read_text(encoding="utf-8"))
    if dataset.get("split") != "pilot_only_no_research_split":
        raise ValueError("pilot source must be explicitly segregated")
    models = [
        {"name": "qwen3.5:2b", "provider": "ollama-local",
         "version": "324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df",
         "context_window": 4096, "capabilities": ["thinking"],
         "metadata": {"quantization": "Q8_0", "pilot_only": True}},
        {"name": "gemma3:4b", "provider": "ollama-local",
         "version": "a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a",
         "context_window": 4096, "capabilities": [],
         "metadata": {"quantization": "Q4_K_M", "pilot_only": True}},
    ]
    spec = {
        "experiment_id": "phase3b-engineering-pilot-v1",
        "dataset_id": dataset["dataset_id"], "dataset_version": dataset["dataset_version"],
        "dataset_hash": _sha(source), "models": models, "cases": dataset["cases"],
        "generation": {"temperature": 0.0, "max_new_tokens": 32, "timeout_seconds": 90},
        "seeds": [2026], "repetitions": 1,
        "measurement": {
            "behavior_representation_version": "not_validated_pilot",
            "layer1_version": None, "layer2_judge_version": None,
            "prompt_version": "pilot_harmless_v1", "rubric_version": None,
            "measurement_version": "not_validated_pilot", "threat_model": "synthetic_instruction_following",
        },
        "preregistration_id": "local-pilot-freeze-v1",
        "specification_version": "controlled-trajectory-v1",
        "metadata": {"evidence_class": "engineering_pilot", "scientific_eligibility": False,
                     "split": "pilot_only_no_research_split", "human_labels": "none"},
        "canary_policy": {"enabled": False},
    }
    encoded = (json.dumps(spec, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if specification.exists():
        if specification.read_bytes() != encoded:
            raise FileExistsError("existing pilot specification differs; create an amendment, never overwrite")
    else:
        with specification.open("xb") as handle:
            handle.write(encoded)
    lock_value = {
        "protocol_id": "local-pilot-freeze-v1", "preregistration_id": "local-pilot-freeze-v1",
        "experiment_id": spec["experiment_id"], "status": "locally_frozen",
        "external_registration": False, "evidence_class": "engineering_pilot",
        "dataset_sha256": _sha(source), "specification_sha256": _sha(specification),
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "amendment_policy": "new version and explicit reason; never overwrite this lock",
    }
    if lock.exists():
        existing = json.loads(lock.read_text(encoding="utf-8"))
        if any(existing.get(key) != lock_value[key] for key in
               ("protocol_id", "experiment_id", "status", "dataset_sha256", "specification_sha256")):
            raise FileExistsError("existing local lock differs; create a versioned amendment")
    else:
        with lock.open("x", encoding="utf-8") as handle:
            json.dump(lock_value, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return {"dataset_sha256": _sha(source), "specification_sha256": _sha(specification),
            "protocol_lock_sha256": _sha(lock)}


if __name__ == "__main__":
    print(json.dumps(prepare(), sort_keys=True))
