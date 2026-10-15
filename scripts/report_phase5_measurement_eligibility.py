"""Report evidence/applicability gates without calculating safety scores."""

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

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.experiments.runner import ObservationStore
from core.persistence.database import make_engine
from core.persistence.models import ScientificRecordEntity


def _verified_human_record(row: ScientificRecordEntity, manifest_sha256: str,
                           rubric_sha256: dict[str, str]) -> bool:
    provenance = row.provenance or {}
    source = Path(str(provenance.get("source_artifact", "")))
    expected = provenance.get("source_sha256")
    if (provenance.get("fixture") is not False
            or provenance.get("data_origin") != "human_annotation"
            or provenance.get("package_manifest_sha256") != manifest_sha256
            or provenance.get("rubric_sha256") != rubric_sha256
            or not provenance.get("batch_id") or not provenance.get("label_version")
            or not isinstance(expected, str) or not source.is_file()
            or hashlib.sha256(source.read_bytes()).hexdigest() != expected):
        return False
    return (row.family != "attack_outcome" or
            row.payload.get("label_source") in {
                "human_adjudication", "independent_human_agreement"})


def report(phase4: Path, annotation_db: Path | None = None) -> dict[str, object]:
    observations = ObservationStore(phase4 / "jbb_pilot_run_v1" / "observations").all()
    conditions = Counter(item.condition.value for item in observations)
    attack_ids = {item.observation_id for item in observations
                  if item.condition.value in {"isolated_attack", "sequential_attack"}
                  and item.status.value == "completed"}
    human_rows = outcome_rows = 0
    reviewers_by_observation: dict[str, set[str]] = {}
    final_by_observation: dict[str, int] = {}
    verified_by_observation: dict[str, bool] = {}
    label_identities: set[tuple[str, str]] = set()
    if annotation_db is not None and annotation_db.is_file():
        package = ROOT / "experiments" / "phase5" / "restricted_annotation_v2"
        manifest_bytes = (package / "package_manifest.json").read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        rubric_sha256 = json.loads(manifest_bytes)["rubric_sha256"]
        engine = make_engine(f"sqlite:///{annotation_db.resolve()}")
        try:
            with Session(engine) as session:
                for row in session.scalars(select(ScientificRecordEntity).where(
                        ScientificRecordEntity.owner_id.in_(attack_ids))):
                    if row.family not in {"human_annotation", "human_adjudication", "attack_outcome"}:
                        continue
                    if row.provenance.get("fixture") is True:
                        continue
                    label_identities.add((str(row.provenance.get("batch_id", "")),
                                          str(row.provenance.get("label_version", ""))))
                    verified_by_observation[row.owner_id] = (
                        verified_by_observation.get(row.owner_id, True)
                        and _verified_human_record(row, manifest_sha256, rubric_sha256))
                    if row.family == "human_annotation":
                        human_rows += 1
                        reviewers_by_observation.setdefault(row.owner_id, set()).add(
                            str(row.payload.get("rater_id", "")))
                    elif row.family == "attack_outcome":
                        outcome_rows += 1
                        final_by_observation[row.owner_id] = final_by_observation.get(row.owner_id, 0) + 1
        finally:
            engine.dispose()
    if len(observations) != 100 or len(attack_ids) != 36:
        raise ValueError("saved Phase 4 exploratory run differs from audited 100/36 observations")
    complete_human_outcomes = (set(final_by_observation) == attack_ids
        and all(count == 1 for count in final_by_observation.values())
        and set(reviewers_by_observation) == attack_ids
        and all(len(raters) == 2 and "" not in raters
                for raters in reviewers_by_observation.values())
        and set(verified_by_observation) == attack_ids
        and all(verified_by_observation.values())
        and len(label_identities) == 1)
    return {
        "report_version": "phase5-measurement-eligibility-v1",
        "experiment_id": "phase4-jbb-exploratory-pilot-v1",
        "evidence_class": "exploratory",
        "observations": len(observations), "completed_attack_responses": len(attack_ids),
        "condition_counts": dict(conditions),
        "human_judgment_rows": human_rows, "final_human_outcome_rows": outcome_rows,
        "measurements": {
            "operational_execution": {"status": "available", "validation": "exploratory",
                "reason": "persisted responses, conditions and metadata; not a safety outcome"},
            "ASR": {"status": "exploratory" if complete_human_outcomes else "blocked",
                "validation": "not_validated",
                "reason": "complete independent human outcomes are absent" if not complete_human_outcomes else
                          "complete human outcomes exist but claim-specific review and held-out status are not certified"},
            "BSDA": {"status": "uncalibrated", "validation": "not_validated",
                "reason": "no validated semantic/safety/instruction representations or component calibration for this run"},
            "RC": {"status": "undefined", "validation": "not_validated",
                "reason": "no validated behavioral states or recovery calibration; repeated harmful-goal probes lack validation"},
            "SAEA": {"status": "blocked", "validation": "not_validated",
                "reason": "no validated state vectors; isolated provider sessions are unverifiable"},
        },
        "validated_scientific_metrics": [],
        "model_ranking_eligible": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase4", type=Path, default=ROOT / "experiments" / "phase4")
    parser.add_argument("--annotation-db", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = report(args.phase4, args.annotation_db)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "reported_without_scoring", "observations": value["observations"],
                      "validated_scientific_metrics": value["validated_scientific_metrics"]}, sort_keys=True))
