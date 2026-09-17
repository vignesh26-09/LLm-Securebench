"""Run an explicit controlled trajectory specification against local Ollama."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.experiments.manifest import build_manifest, stable_hash
from core.experiments.models import ExperimentSpecification
from core.experiments.runner import ExperimentRunner, ObservationStore
from core.experiments.persistence import append_scientific_artifact
from core.experiments.specification import load_experiment_specification
from core.inference.ollama_provider import OllamaProvider, installed_models
from core.persistence.database import make_engine
from core.persistence.models import ScientificRecordEntity
from sqlalchemy.orm import Session


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("specification", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=ROOT / "securellmbench.db")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    spec = load_experiment_specification(args.specification)
    inventory = {item["name"]: item for item in installed_models()}
    resolved = []
    for model in spec.models:
        if model.provider != "ollama-local":
            raise SystemExit("This safe CLI supports only already-installed local Ollama models")
        if model.name not in inventory:
            raise SystemExit(f"Ollama model is not installed: {model.name}")
        actual = inventory[model.name]
        actual_digest = actual.get("digest")
        if model.version is not None and actual_digest is not None and model.version != actual_digest:
            raise SystemExit(f"Model digest differs from specification: {model.name}")
        resolved.append(replace(model, version=actual_digest or model.version))
    spec = replace(spec, models=tuple(resolved))
    start = datetime.now(timezone.utc).isoformat()
    store = ObservationStore(args.output / "observations")
    observations = ExperimentRunner(OllamaProvider(), store).run(spec, force=args.force)
    end = datetime.now(timezone.utc).isoformat()
    files = sorted((args.output / "observations").glob("*.json"))
    hashes = {str(path.relative_to(args.output)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    all_observations = store.all()
    manifest = build_manifest(spec, all_observations, root=str(ROOT), experiment_start=start,
                              experiment_end=end, artifact_hashes=hashes)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists() and not args.force:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("experiment_id") != spec.experiment_id:
            raise SystemExit("output contains a different experiment manifest")
    else:
        manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8")
    _persist(args.database, spec, all_observations, manifest)
    print(json.dumps({"experiment_id": spec.experiment_id, "observations": len(observations),
                      "successful": manifest.successful_count, "failed": manifest.failed_count,
                      "manifest": str(manifest_path)}))


def _persist(database: Path, spec, observations, manifest) -> None:
    engine = make_engine(f"sqlite:///{database}")
    try:
        with Session(engine) as session:
            _append_if_absent(session, f"experiment:{spec.experiment_id}:specification",
                "experiment_specification", "controlled-trajectory-v1", "experiment", spec.experiment_id,
                "declared", spec, {"source": "run_controlled_experiment.py"})
            for observation in observations:
                _append_if_absent(session, f"experiment:{spec.experiment_id}:observation:{observation.observation_id}",
                    "experimental_condition", "controlled-trajectory-v1", "evaluation", observation.evaluation_case_id,
                    observation.status.value, observation, {"experiment_id": spec.experiment_id})
                if observation.control_identity is not None:
                    _append_if_absent(session, f"experiment:{spec.experiment_id}:control:{observation.observation_id}",
                        "control_match_identity", "control-match-v1", "evaluation", observation.evaluation_case_id,
                        "declared", observation.control_identity, {"observation_id": observation.observation_id})
            _append_if_absent(session, f"experiment:{spec.experiment_id}:manifest",
                "reproducibility_manifest", "manifest-v1", "experiment", spec.experiment_id,
                "recorded", manifest, {"source": "run_controlled_experiment.py"})
    finally:
        engine.dispose()


def _append_if_absent(session, record_id, family, schema_version, scope, owner_id, status, artifact, provenance):
    if session.get(ScientificRecordEntity, record_id) is None:
        append_scientific_artifact(session, record_id=record_id, family=family,
            schema_version=schema_version, scope=scope, owner_id=owner_id,
            status=status, artifact=artifact, provenance=provenance)


if __name__ == "__main__":
    main()
