"""Synthetic evidence projections: no inference, no independent-calibration claims."""
import copy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app
from apps.api.metric_compute import stored_metric_evidence
from core.persistence.models import ScientificRecordEntity


def record(family, payload, status="computed", provenance=None):
    return SimpleNamespace(id="synthetic-evidence", family=family, status=status,
                           schema_version="synthetic-v1", scope="SYNTHETIC_TEST",
                           payload=payload, provenance=provenance if provenance is not None else {
                               "protocol": "synthetic-fixture", "source_sha256": "a" * 64, "units": "ms"})


@pytest.mark.parametrize("metric,family,payload,status,expected", [
    ("bsda", "bsda", {"components": {"semantic": {"raw_distance": .25}, "safety": {"raw_distance": 0}}}, "component_vector_computed", [.25, 0]),
    ("recovery", "rc", {"delta_a": .8, "recovery_deltas": [[1, .4], [2, None]]}, "uncalibrated", [.8, .4]),
    ("saea", "saea", {"per_step": [{"position": 1, "context_effect": -.2, "status": "applicable"}, {"position": 2, "context_effect": .9, "status": "failed_evaluation"}]}, "applicable", [-.2]),
    ("draa", "draa", {"features": [{"status": "applicable"}, {"status": "failed"}], "risk_score": None}, "uncalibrated", [1, 1]),
    ("pri", "pri", {"coverage": {"requested_categories": ["fake-a", "fake-b"], "observed_categories": ["fake-a"]}, "cells": [], "scalar_pri": None}, "uncalibrated", [2, 1, 0]),
    ("dqi", "dqi", {"components": {"coverage": .75, "novelty": 0}, "score": None, "reason": "semantic_embeddings_unavailable"}, "unavailable", [.75]),
    ("statistics", "statistics", {"values": {"minimum": 1, "mean": 3, "maximum": 5, "sample_variance": None}}, "computed", [1, 3, 5]),
    ("ml", "ml", {"metrics": {"fake-estimator": {"accuracy": {"value": .6}}}}, "completed", [.6]),
    ("mchl", "mchl", {"complete_context_valid_pairs": 2, "adversarial_rate_complete": .5, "benign_rate_complete": 0, "complete_pair_lift": .5}, "computed", [.5, 0, .5]),
])
def test_metric_projection_preserves_only_measured_source_values(metric, family, payload, status, expected):
    source = record(family, payload, status)
    before = copy.deepcopy(source.__dict__)
    output = stored_metric_evidence(metric, source)
    values = [p["value"] for s in output["series"] for p in s["points"] if p["value"] is not None]
    assert values == expected
    assert output["scientific_calibration"] == "not_established"
    assert output["provenance"]["source_sha256"] == "a" * 64
    assert source.__dict__ == before
    assert "risk_score" not in output and "scalar_pri" not in output


@pytest.mark.parametrize("status", ["failed", "failed_evaluation", "undefined", "blocked", None])
def test_failed_or_missing_status_never_becomes_a_numeric_pass(status):
    output = stored_metric_evidence("statistics", record("statistics", {"values": {"mean": 999}}, status))
    assert output["series"] == []
    assert any("not a safe/pass result" in reason for reason in output["unavailable"])


def test_null_boolean_nonfinite_values_and_missing_provenance_remain_unavailable():
    output = stored_metric_evidence("bsda", record("bsda", {"components": {
        "semantic": {"raw_distance": float("nan")}, "safety": {"raw_distance": True},
        "instruction": {"raw_distance": .9, "unmeasurable": True}, "structural": {"raw_distance": None}}}, provenance={}))
    assert all(p["value"] is None and p["reason"] for p in output["series"][0]["points"])
    assert any("Source provenance unavailable" in reason for reason in output["unavailable"])


def test_projection_redacts_free_text_and_never_establishes_caller_calibration():
    output = stored_metric_evidence("recovery", record("rc", {"delta_a": .5, "calibration_artifact": {"artifact_id": "unverified"}}, "uncalibrated",
        {"units": "distance", "source_sha256": "b" * 64, "password": "synthetic-not-a-secret", "raw_response": "synthetic output"}))
    assert set(output["provenance"]) == {"units", "source_sha256"}
    assert output["scientific_calibration"] == "not_established"
    assert all(p["value"] is None for p in output["series"][1]["points"])


def test_evidence_api_is_paginated_read_only_and_preserves_recovery_aliases(tmp_path):
    app = create_app(f"sqlite:///{(tmp_path / 'metric-evidence.db').as_posix()}")
    factory = app.state.session_factory
    try:
        with factory() as session, session.begin():
            for identity, family in (("fixture-a", "rc"), ("fixture-b", "recovery")):
                session.add(ScientificRecordEntity(id=identity, family=family, schema_version="fixture-v1", scope="SYNTHETIC_TEST",
                    status="uncalibrated", payload={"delta_a": .5, "recovery_deltas": [[1, .3]]}, provenance={"protocol": "synthetic-test"}))
        with TestClient(app) as client:
            first = client.get("/metrics/compute/recovery/evidence?limit=1").json()
            second = client.get("/metrics/compute/recovery/evidence?limit=1&offset=1").json()
            assert first["total"] == second["total"] == 2
            assert first["records"][0]["id"] != second["records"][0]["id"]
            assert first["records"][0]["status"] == "uncalibrated"
            assert client.get("/metrics/compute/mchl/evidence").json()["records"] == []
            assert client.get("/metrics/compute/unknown/evidence").status_code == 404
            assert client.get("/metrics/compute/bsda/evidence?limit=101").status_code == 422
            assert client.get("/metrics/compute/bsda/evidence?offset=-1").status_code == 422
        with factory() as session:
            assert session.get(ScientificRecordEntity, "fixture-a").payload == {"delta_a": .5, "recovery_deltas": [[1, .3]]}
    finally:
        factory.kw["bind"].dispose()


def test_evidence_endpoint_keeps_existing_api_auth_protection(tmp_path):
    app = create_app(f"sqlite:///{(tmp_path / 'protected.db').as_posix()}", require_auth=True)
    try:
        with TestClient(app) as client:
            assert client.get("/metrics/compute/statistics/evidence").status_code == 401
    finally:
        app.state.session_factory.kw["bind"].dispose()
