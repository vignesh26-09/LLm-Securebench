"""Audit an engineering pilot without deriving scientific model scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.experiments.contamination import ContaminationLedgerStore
from core.experiments.runner import ObservationStore
from core.persistence.database import make_engine
from core.persistence.models import ScientificRecordEntity
from sqlalchemy import select
from sqlalchemy.orm import Session


def audit(run_dir: Path, database: Path, *, expected_class: str = "engineering_pilot") -> dict[str, object]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("evidence_layer_status", {}).get("evidence_class") != expected_class:
        raise ValueError("run evidence class does not match requested audit")
    for relative, expected_hash in manifest["artifact_hashes"].items():
        actual = hashlib.sha256((run_dir / relative).read_bytes()).hexdigest()
        if actual != expected_hash:
            raise ValueError(f"observation hash mismatch: {relative}")
    observations = ObservationStore(run_dir / "observations").all()
    if len(observations) != len(manifest["artifact_hashes"]):
        raise ValueError("observation inventory differs from manifest")
    engine = make_engine(f"sqlite:///{database}")
    try:
        with Session(engine) as session:
            records = session.scalars(select(ScientificRecordEntity).where(
                ScientificRecordEntity.family == "experimental_condition",
                ScientificRecordEntity.id.like(f"experiment:{manifest['experiment_id']}:observation:%")
            )).all()
            if len(records) != len(observations):
                raise ValueError("pilot database and observation inventory differ")
            if any((record.provenance or {}).get("reporting_class") != expected_class
                   or (record.provenance or {}).get("synthetic") is not (expected_class == "engineering_pilot")
                   for record in records):
                raise ValueError("pilot record provenance does not match its evidence class")
    finally:
        engine.dispose()
    ledger = ContaminationLedgerStore(run_dir / "contamination-ledger").all()
    return {
        "status": "engineering_pilot_only" if expected_class == "engineering_pilot" else "exploratory_unlabeled",
        "experiment_id": manifest["experiment_id"],
        "dataset": manifest["dataset_identity"],
        "source_observation_count": len(observations), "database_observation_count": len(records),
        "counts_by_model": dict(Counter(item.target_model for item in observations)),
        "counts_by_condition": dict(Counter(item.condition.value for item in observations)),
        "counts_by_status": dict(Counter(item.status.value for item in observations)),
        "counts_by_context_status": dict(Counter(item.context_status.value for item in observations)),
        "counts_by_canary_status": dict(Counter((item.canary_evidence or {}).get("status", "unknown")
                                             for item in observations)),
        "isolation_ledger": dict(Counter(item.status.value for item in ledger)),
        "first_observation_at": min((item.timestamp for item in observations), default=None),
        "last_observation_at": max((item.timestamp for item in observations), default=None),
        "human_labels": 0, "scientific_metrics": "insufficient_data",
        "scientific_reason": ("synthetic pilot task" if expected_class == "engineering_pilot"
                              else "real-source exploratory pilot") +
                             "; no independent human labels or validated behavioral states",
        "manifest_sha256": hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run_dir, args.database)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
