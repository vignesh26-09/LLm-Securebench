"""Synthetic form tests and read-only audits; no research labels are created."""

import csv
import hashlib
import io
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.evaluation.phase5_annotation import (
    audit_annotation_batch, form_csv, independent_agreement, judgments_from_forms,
)
from core.evaluation import phase5_annotation
from core.evaluation.annotation_workflow import persist_annotation_import, validate_annotation_import
from core.experiments.persistence import append_scientific_artifact
from core.experiments.runner import ObservationStore
from core.persistence.database import Base, make_engine
from core.persistence.models import ScientificRecordEntity
from sqlalchemy.orm import Session
from scripts.import_phase5_annotation import run as import_run
from scripts.import_phase5_annotation import verify_package
from scripts.prepare_phase5_annotation import prepare
from scripts.report_phase5_measurement_eligibility import report as eligibility_report
from scripts.report_phase5_measurement_eligibility import _verified_human_record
from scripts.report_phase5_source_pool import report as source_pool_report
from scripts.prepare_phase6_adjudication import disagreement_rows


ROOT = Path(__file__).resolve().parents[1]
PHASE4 = ROOT / "experiments" / "phase4"
RESTRICTED = PHASE4 / "restricted_annotation"


def paths():
    return dict(
        observations_dir=PHASE4 / "jbb_pilot_run_v1" / "observations",
        objectives_path=PHASE4 / "jbb_annotation_objectives_v1.json",
        candidates_path=RESTRICTED / "candidates_v1.json",
        public_path=RESTRICTED / "blinded_batch_v1.json",
        private_path=RESTRICTED / "private_join_map_v1.json",
    )


def synthetic_public():
    return {"items": [{"sample_id": "synthetic-sample", "legitimate_task": "Say hello",
                       "adversarial_objective": "Include a harmless marker",
                       "conversation_history": [{"role": "user", "content": "Hello"},
                                                {"role": "assistant", "content": "Hello marker"}],
                       "target_response": "Hello marker"}]}


def filled_form(tmp_path, name, rater, outcome, *, change_context=False):
    rows = list(csv.DictReader(io.StringIO(form_csv(synthetic_public()).decode("utf-8-sig"))))
    row = rows[0]
    row["rater_id"] = rater
    row["outcome"] = outcome
    row["rationale"] = "Synthetic harmless fixture rationale"
    if change_context:
        row["context_before_response"] = "[]"
    path = tmp_path / name
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return path


def test_real_batch_has_36_exact_source_matches_without_labels():
    report = audit_annotation_batch(**paths())
    assert report["status"] == "source_verified_reviewer_ready_unlabeled"
    assert report["completed_attack_observations"] == 36
    assert report["blinded_sample_count"] == 36
    assert report["duplicate_evaluation_ids"] == 0
    assert report["duplicate_sample_ids"] == 0
    assert report["duplicate_exact_content_groups"] == 0
    assert report["missing_context_count"] == 0
    assert report["missing_objective_count"] == 0
    assert report["source_hash_mismatches"] == 0
    assert report["human_label_count"] == 0


def test_tampered_candidate_response_is_rejected(tmp_path):
    original = json.loads(paths()["candidates_path"].read_text(encoding="utf-8"))
    original["candidates"][0]["target_response"] = "tampered synthetic fixture text"
    altered = tmp_path / "candidates.json"
    altered.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="candidate differs"):
        audit_annotation_batch(**{**paths(), "candidates_path": altered})


def test_run_manifest_hash_mismatch_is_rejected():
    actual_read = phase5_annotation._read

    def altered_read(path):
        value = actual_read(path)
        if path.name == "manifest.json":
            first = next(iter(value["artifact_hashes"]))
            value["artifact_hashes"][first] = "0" * 64
        return value

    with patch.object(phase5_annotation, "_read", side_effect=altered_read):
        with pytest.raises(ValueError, match="saved observation differs from run manifest"):
            audit_annotation_batch(**paths())


def test_reviewer_forms_blank_separate_and_immutable(tmp_path):
    value = prepare(PHASE4, tmp_path / "package")
    assert value["samples"] == 36
    package = tmp_path / "package"
    a = (package / "reviewer_a.csv").read_bytes()
    b = (package / "reviewer_b.csv").read_bytes()
    assert a == b
    rows = list(csv.DictReader(io.StringIO(a.decode("utf-8-sig"))))
    assert len(rows) == 36
    assert all(not row["outcome"] and not row["rater_id"] and not row["rationale"] for row in rows)
    assert len({row["sample_id"] for row in rows}) == 36
    manifest = json.loads((package / "package_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "blank_forms_no_human_judgments"
    assert manifest["package_version"] == "phase5-independent-review-v2"
    assert manifest["form_sha256"]["reviewer_a.csv"] == hashlib.sha256(a).hexdigest()
    assert len(manifest["rubric_sha256"]) == 3
    assert all((package / path).is_file() for path in manifest["rubric_sha256"])
    assert prepare(PHASE4, package) == value
    (package / "reviewer_a.csv").write_bytes(a + b"tampered")
    with pytest.raises(FileExistsError, match="immutable annotation package"):
        prepare(PHASE4, package)


def test_synthetic_filled_forms_require_independent_ids_complete_labels_and_unchanged_context(tmp_path):
    public = synthetic_public()
    a = filled_form(tmp_path, "a.csv", "synthetic-r1", "failure")
    b = filled_form(tmp_path, "b.csv", "synthetic-r2", "success")
    rows = judgments_from_forms(public, a, b)
    assert len(rows) == 2
    agreement = independent_agreement(rows)
    assert agreement["sample_count"] == 1
    assert agreement["agreement"] == 0
    assert agreement["disagreements"] == 1
    assert agreement["cohen_kappa"] == 0
    handoff = disagreement_rows(public, rows)
    assert len(handoff) == 1
    assert handoff[0]["sample_id"] == "synthetic-sample"
    assert handoff[0]["reviewer_a_outcome"] == "failure"
    assert handoff[0]["reviewer_b_outcome"] == "success"
    assert handoff[0]["context_before_response"] == '[{"role": "user", "content": "Hello"}]'
    same = filled_form(tmp_path, "same.csv", "synthetic-r1", "failure")
    with pytest.raises(ValueError, match="independent rater IDs"):
        judgments_from_forms(public, a, same)
    changed = filled_form(tmp_path, "changed.csv", "synthetic-r3", "failure", change_context=True)
    with pytest.raises(ValueError, match="changes source context"):
        judgments_from_forms(public, a, changed)
    blank = tmp_path / "blank.csv"
    blank.write_bytes(form_csv(public))
    with pytest.raises(ValueError, match="nonempty pseudonymous rater ID"):
        judgments_from_forms(public, a, blank)


def test_real_blank_forms_cannot_be_imported(tmp_path):
    package = ROOT / "experiments" / "phase5" / "restricted_annotation_v2"
    with pytest.raises(ValueError, match="nonempty pseudonymous rater ID"):
        import_run(phase4=PHASE4, reviewer_a=package / "reviewer_a.csv",
                   reviewer_b=package / "reviewer_b.csv",
                   adjudications=package / "adjudication_template.csv",
                   label_version="synthetic-test-only", database=tmp_path / "must-not-exist.db")
    assert not (tmp_path / "must-not-exist.db").exists()


def test_import_verifies_immutable_package_and_rubric_hashes(tmp_path):
    package = ROOT / "experiments" / "phase5" / "restricted_annotation_v2"
    public = RESTRICTED / "blinded_batch_v1.json"
    private = RESTRICTED / "private_join_map_v1.json"
    evidence = verify_package(package, public_path=public, private_path=private,
                              batch_id="phase4-jbb-pilot-v1", sample_count=36)
    assert len(evidence["package_manifest_sha256"]) == 64
    assert len(evidence["rubric_sha256"]) == 3
    altered = tmp_path / "package"
    shutil.copytree(package, altered)
    rubric = altered / "rubrics" / "PHASE5_HUMAN_REVIEW_PROTOCOL.md"
    rubric.write_bytes(rubric.read_bytes() + b"\nsynthetic tamper\n")
    with pytest.raises(ValueError, match="annotation package file or hash differs"):
        verify_package(altered, public_path=public, private_path=private,
                       batch_id="phase4-jbb-pilot-v1", sample_count=36)


def test_real_pilot_metric_report_preserves_unavailable_values(tmp_path):
    value = eligibility_report(PHASE4, tmp_path / "no-human-labels.db")
    assert value["observations"] == 100
    assert value["completed_attack_responses"] == 36
    assert value["human_judgment_rows"] == 0
    assert value["final_human_outcome_rows"] == 0
    assert value["measurements"]["ASR"]["status"] == "blocked"
    assert value["measurements"]["BSDA"]["status"] == "uncalibrated"
    assert value["measurements"]["RC"]["status"] == "undefined"
    assert value["measurements"]["SAEA"]["status"] == "blocked"
    assert value["validated_scientific_metrics"] == []
    assert value["model_ranking_eligible"] is False


def test_partial_annotation_records_cannot_unlock_asr(tmp_path):
    attack = next(item for item in ObservationStore(
        PHASE4 / "jbb_pilot_run_v1" / "observations").all()
        if item.condition.value in {"isolated_attack", "sequential_attack"})
    database = tmp_path / "synthetic_partial.db"
    engine = make_engine(f"sqlite:///{database}")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            append_scientific_artifact(session, record_id="synthetic-partial-outcome",
                family="attack_outcome", schema_version="synthetic-test", scope="evaluation",
                owner_id=attack.observation_id, status="classified",
                artifact={"success": True}, provenance={"fixture": False})
        report = eligibility_report(PHASE4, database)
        assert report["final_human_outcome_rows"] == 1
        assert report["measurements"]["ASR"]["status"] == "blocked"
    finally:
        engine.dispose()


def test_asr_gate_requires_source_and_human_package_provenance(tmp_path):
    source = tmp_path / "synthetic-source.txt"
    source.write_text("harmless synthetic source", encoding="utf-8")
    provenance = {"fixture": False, "data_origin": "human_annotation",
                  "source_artifact": str(source),
                  "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "package_manifest_sha256": "synthetic-manifest",
                  "rubric_sha256": {"synthetic-rubric": "synthetic-hash"},
                  "batch_id": "synthetic-batch", "label_version": "synthetic-v1"}
    row = SimpleNamespace(family="attack_outcome",
                          payload={"label_source": "independent_human_agreement"},
                          provenance=provenance)
    assert _verified_human_record(row, "synthetic-manifest",
                                  {"synthetic-rubric": "synthetic-hash"})
    row.payload["label_source"] = "automated_judge"
    assert not _verified_human_record(row, "synthetic-manifest",
                                      {"synthetic-rubric": "synthetic-hash"})
    row.payload["label_source"] = "human_adjudication"
    source.write_text("changed", encoding="utf-8")
    assert not _verified_human_record(row, "synthetic-manifest",
                                      {"synthetic-rubric": "synthetic-hash"})


def test_proposed_source_pool_excludes_calibration_near_overlaps_and_pilot():
    value = source_pool_report()
    assert value["aligned_source_goals"] == 79
    assert value["candidate_goal_count"] == 66
    assert value["exact_split_frozen"] is False
    assert set(value["candidate_goal_ids"]).isdisjoint(
        value["historical_calibration_near_overlap_ids"] + value["used_exploratory_pilot_ids"])
    assert sum(value["candidate_by_category"].values()) == 66
    assert len(value["candidate_by_category"]) == 10


def test_synthetic_forms_adjudicate_preserve_partial_and_reject_duplicate_import(tmp_path):
    public = {**synthetic_public(), "schema_version": "human-annotation-v1",
              "batch_id": "synthetic-phase5", "rubric_version": "synthetic-rubric"}
    private = {"schema_version": "human-annotation-map-v1", "batch_id": "synthetic-phase5",
               "rubric_version": "synthetic-rubric", "mapping": {
                   "synthetic-sample": {"evaluation_id": "synthetic-evaluation",
                                        "attack_family": "synthetic", "source_artifact": "synthetic-only",
                                        "source_sha256": "synthetic-only", "synthetic_fixture": True}}}
    a = filled_form(tmp_path, "a.csv", "synthetic-r1", "failure")
    b = filled_form(tmp_path, "b.csv", "synthetic-r2", "success")
    judgments = judgments_from_forms(public, a, b)
    with pytest.raises(ValueError, match="disagreement requires adjudication"):
        validate_annotation_import(public, private, judgments, [], label_version="synthetic-v1")
    adjudications = [{"sample_id": "synthetic-sample", "adjudicator_id": "synthetic-r3",
                      "outcome": "partial", "rationale": "Synthetic fixture uncertainty"}]
    validated = validate_annotation_import(public, private, judgments, adjudications,
                                           label_version="synthetic-v1")
    assert validated["disagreements"] == 1
    engine = make_engine(f"sqlite:///{tmp_path / 'synthetic.db'}")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            persist_annotation_import(session, validated, private,
                                      extra_provenance={"package_manifest_sha256": "synthetic-package-hash",
                                                        "rubric_sha256": {"synthetic-rubric": "synthetic-hash"}})
            outcome = session.get(ScientificRecordEntity,
                                  "human-outcome:synthetic-v1:synthetic-evaluation")
            assert outcome.payload["success"] is None
            assert outcome.payload["reason"] == "partial"
            assert outcome.provenance["fixture"] is True
            assert outcome.provenance["package_manifest_sha256"] == "synthetic-package-hash"
            assert outcome.provenance["rubric_sha256"]["synthetic-rubric"] == "synthetic-hash"
            with pytest.raises(ValueError, match="immutable scientific artifact already exists"):
                persist_annotation_import(session, validated, private)
    finally:
        engine.dispose()
