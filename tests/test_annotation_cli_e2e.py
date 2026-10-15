"""End-to-end synthetic fixture transport; never evidence of real human review."""

import json
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.persistence.models import ScientificRecordEntity


def test_synthetic_annotation_export_import_cli(tmp_path):
    root = Path(__file__).resolve().parents[1]
    candidate = tmp_path / "candidates.json"
    candidate.write_text(json.dumps({"synthetic_fixture": True, "candidates": [{
        "evaluation_id": "synthetic-cli-1", "legitimate_task": "Synthetic harmless task",
        "adversarial_objective": "Include synthetic marker", "target_response": "Sample response",
        "conversation_history": [{"role": "user", "content": "Synthetic prompt", "model": "blinded"}],
        "attack_family": "synthetic", "source_artifact": "synthetic-only",
        "source_sha256": "synthetic-fixture"}]}), encoding="utf-8")
    public, private = tmp_path / "public.json", tmp_path / "private.json"
    subprocess.run([sys.executable, str(root / "scripts/annotation_batch.py"), "export",
        "--candidates", str(candidate), "--public", str(public), "--private-map", str(private),
        "--batch-id", "synthetic-cli", "--rubric-version", "synthetic-v1"],
        cwd=root, check=True, capture_output=True, text=True)
    visible = public.read_text(encoding="utf-8")
    assert "synthetic-cli-1" not in visible
    assert "blinded" not in visible
    sample = json.loads(visible)["items"][0]["sample_id"]
    judgments = tmp_path / "judgments.json"
    judgments.write_text(json.dumps([
        {"sample_id": sample, "rater_id": "synthetic-r1", "outcome": "failure", "rationale": "Synthetic only"},
        {"sample_id": sample, "rater_id": "synthetic-r2", "outcome": "success", "rationale": "Synthetic only"}]), encoding="utf-8")
    adjudications = tmp_path / "adjudications.json"
    adjudications.write_text(json.dumps([{"sample_id": sample, "adjudicator_id": "synthetic-r3",
        "outcome": "ambiguous", "rationale": "Synthetic disagreement"}]), encoding="utf-8")
    database = tmp_path / "synthetic.db"
    command = [sys.executable, str(root / "scripts/annotation_batch.py"), "import",
        "--public", str(public), "--private-map", str(private),
        "--judgments", str(judgments), "--adjudications", str(adjudications),
        "--label-version", "synthetic-v1", "--database", str(database)]
    subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    engine = create_engine(f"sqlite:///{database}")
    try:
        with Session(engine) as session:
            records = list(session.scalars(select(ScientificRecordEntity)))
            assert len(records) == 4
            assert {row.family for row in records} == {"human_annotation", "human_adjudication", "attack_outcome"}
            assert all(row.provenance["fixture"] is True for row in records)
            outcome = next(row for row in records if row.family == "attack_outcome")
            assert outcome.payload["success"] is None
            assert outcome.payload["reason"] == "ambiguous"
    finally:
        engine.dispose()
    again = subprocess.run(command, cwd=root, capture_output=True, text=True)
    assert again.returncode != 0
