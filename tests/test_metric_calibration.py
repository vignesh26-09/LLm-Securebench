"""Synthetic calibration evidence: never establish claims from mere record counts."""
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.api import metric_calibration as calibration
from apps.api.main import create_app
from apps.api.metric_compute import stored_metric_evidence
from core.persistence.models import ScientificRecordEntity


@pytest.fixture(autouse=True)
def isolated_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(calibration, "ROOT", tmp_path)


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_narrow_scope_requires_every_criterion_and_explicit_scope():
    yes = calibration.criterion("Synthetic explicit gate", True, 2, 2, "synthetic-plan.json")
    assert calibration.summarize_calibration([yes], None)["status"] == "not_established"
    result = calibration.summarize_calibration([yes], "synthetic narrow test scope, 2 observations")
    assert result["status"] == "established"
    assert result["scope"] == "synthetic narrow test scope, 2 observations"
    for value in (False, None):
        gate = {**yes, "met": value}
        output = calibration.summarize_calibration([gate], "synthetic narrow scope")
        assert output["status"] == "not_established" and output["scope"] is None
        assert output["missing_evidence"] == [gate["text"]]


def test_counts_cannot_authenticate_review_or_scientific_claim(tmp_path):
    row = SimpleNamespace(status="computed")
    for n in (0, 100):
        result = calibration.build_calibration("bsda", [row], [], n, tmp_path)
        assert result["status"] == "not_established" and result["scope"] is None
        assert result["criteria"][0]["met"] is True
        assert result["criteria"][1]["measured_value"] is None
        assert result["criteria"][-1]["met"] is (False if n == 0 else None)


def test_missing_private_artifacts_never_supply_fake_numbers(tmp_path):
    result = calibration.build_calibration("ml", [], [], 0, tmp_path)
    assert result["artifact_availability"] == "unavailable"
    assert result["artifact_sha256"] == {}
    assert not any("recall" in m["name"] for m in result["measurements"])
    assert all(c["measured_value"] is None for c in result["criteria"][1:3])
    assert any("test_predictions.json" in reason for reason in result["missing_evidence"])


def test_judge_errors_recomputed_with_invalids_never_safe(tmp_path):
    rows = [
        {"ground_truth": "unsafe", "V0": "safe", "V3": "borderline"},
        {"ground_truth": "unsafe", "V0": "invalid", "V3": "unsafe"},
        {"ground_truth": "safe", "V0": "safe", "V3": "unsafe"},
        {"ground_truth": "unavailable", "V0": "safe", "V3": "safe"},
    ]
    write(tmp_path, calibration.DEVTEST + "/test_predictions.json", rows)
    values, hashes, _ = calibration.artifact_measurements(tmp_path)
    measured = {v["name"]: v["value"] for v in values}
    assert measured["V0 test recall"] == 0
    assert measured["V0 test invalid"] == 1
    assert measured["V0 test precision"] is None
    assert measured["V3 test recall"] == 1
    assert measured["V3 test fpr"] == 1
    assert measured["V3 test precision"] == pytest.approx(2 / 3)
    assert hashes and len(next(iter(hashes.values()))) == 64
    assert "Retrospective" in values[0]["scope"]


def test_empty_denominators_remain_null():
    values = calibration.judge_counts([{"ground_truth": "safe", "V0": "safe"}], "V0")
    assert values["recall"] is None and values["precision"] is None
    assert values["fpr"] == 0


def test_pilot_counts_are_read_from_artifacts_not_assumed(tmp_path):
    write(tmp_path, calibration.PILOT + "/state.json", {"pilot": [{"completed": 4, "failed": 1}, {"completed": None, "failed": 0}]})
    values, _, _ = calibration.artifact_measurements(tmp_path)
    measured = {v["name"]: v["value"] for v in values}
    assert measured["Pilot checkpoint completed"] == 4
    assert measured["Pilot checkpoint failed"] == 1


def test_malformed_artifact_is_unavailable_not_a_server_error(tmp_path):
    path = tmp_path / calibration.DEVTEST / "test_predictions.json"
    path.parent.mkdir(parents=True)
    path.write_text("{", encoding="utf-8")
    measurements, _, missing = calibration.artifact_measurements(tmp_path)
    assert measurements == []
    assert any("valid JSON" in reason for reason in missing)


def test_human_and_llm_evidence_are_separate_and_never_factual_truth(tmp_path):
    folder = tmp_path / calibration.LABELS
    (folder / "human_kit").mkdir(parents=True)
    (folder / "human_kit/human_sheet.csv").write_text("\ufeffid,label\na,safe\nb,\n", encoding="utf-8")
    (folder / "llm_labels_pass1.csv").write_text("\ufeffid,label\na,unsafe\n", encoding="utf-8")
    measurements, _, _ = calibration.artifact_measurements(tmp_path)
    values = {m["name"]: m for m in measurements}
    assert values["Human check labeled rows"]["value"] == 1
    assert values["Human check non-safe rows"]["value"] == 0
    assert values["Human check unlabeled or invalid rows"]["value"] == 1
    llm = values["LLM-annotated llm_labels_pass1.csv valid rows"]
    assert llm["value"] == 1 and "not human reference" in llm["scope"]
    assert "not factual-error labels" in values["Human check labeled rows"]["scope"]


@pytest.mark.parametrize("metric", ["bsda", "recovery", "saea", "draa", "pri", "dqi", "mchl", "ml", "statistics", "reviews"])
def test_all_metric_responses_add_calibration_without_changing_old_fields(tmp_path, metric):
    app = create_app(f"sqlite:///{(tmp_path / 'calibration.db').as_posix()}")
    factory = app.state.session_factory
    try:
        with factory() as session, session.begin():
            session.add(ScientificRecordEntity(id="synthetic-measurement", family="statistics", schema_version="synthetic-v1",
                scope="synthetic-test", status="computed", payload={"values": {"mean": 7}}, provenance={"units": "ms"}))
        with TestClient(app) as client:
            response = client.get(f"/metrics/compute/{metric}/evidence")
            assert response.status_code == 200
            body = response.json()
            assert {"metric", "records", "total", "limit", "offset", "scientific_calibration", "evidence_needed"} <= body.keys()
            assert body["calibration"]["status"] == body["scientific_calibration"] == "not_established"
            assert body["calibration"]["missing_evidence"]
            if metric == "statistics":
                with factory() as session:
                    row = session.get(ScientificRecordEntity, "synthetic-measurement")
                    assert body["records"] == [stored_metric_evidence(metric, row)]
                assert body["total"] == 1
    finally:
        factory.kw["bind"].dispose()
