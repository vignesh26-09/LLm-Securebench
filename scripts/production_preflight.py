"""Check whether a supplied corpus and local inventory support a production study.

This script deliberately does not create benchmark cases, labels, or model
results. Those are research inputs that must be approved outside the runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.inference.ollama_provider import InferenceError, installed_models


def assess(raw: dict[str, Any], *, path: Path, inventory: list[dict[str, Any]], requested_models: list[str], minimum_cases: int) -> dict[str, Any]:
    records = raw.get("records") if isinstance(raw.get("records"), list) else []
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    provenance = metadata.get("provenance") if isinstance(metadata.get("provenance"), dict) else {}
    available = {str(item.get("name")) for item in inventory}
    blockers: list[str] = []
    if len(records) < minimum_cases:
        blockers.append(f"dataset_requires_at_least_{minimum_cases}_cases")
    if not metadata.get("source"):
        blockers.append("dataset_source_provenance_missing")
    if not metadata.get("version"):
        blockers.append("dataset_version_missing")
    if not provenance.get("approval_id"):
        blockers.append("dataset_approval_id_missing")
    if not provenance.get("outcome_protocol_id"):
        blockers.append("outcome_protocol_id_missing")
    if not provenance.get("label_schema_id"):
        blockers.append("independent_label_schema_id_missing")
    if not provenance.get("rater_protocol_id"):
        blockers.append("rater_protocol_id_missing")
    missing_models = sorted(set(requested_models) - available)
    if missing_models:
        blockers.append("requested_models_not_installed:" + ",".join(missing_models))
    if len(available) < 2:
        blockers.append("fewer_than_two_local_models_available")
    return {
        "dataset": {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "records": len(records),
                    "categories": sorted({str(item.get("category")) for item in records if isinstance(item, dict) and item.get("category")}),
                    "version": metadata.get("version"), "source": metadata.get("source")},
        "installed_models": sorted(available),
        "requested_models": requested_models,
        "missing_models": missing_models,
        "eligible_for_production_execution": not blockers,
        "blockers": blockers,
        "scientifically_validated": False,
        "notice": "Eligibility is operational only. Independent review and preregistration remain required before scientific claims.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/raw/example.json"))
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--minimum-cases", type=int, default=100)
    args = parser.parse_args()
    if args.minimum_cases < 1:
        raise SystemExit("--minimum-cases must be positive")
    raw = json.loads(args.dataset.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("dataset must be a JSON object containing records and metadata")
    try:
        inventory = installed_models()
    except InferenceError as error:
        raise SystemExit(f"local model inventory unavailable: {error}") from error
    result = assess(raw, path=args.dataset, inventory=inventory, requested_models=args.model, minimum_cases=args.minimum_cases)
    print(json.dumps(result, indent=2))
    if result["blockers"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
