from apps.api.metric_projection import measurements


def test_components_keep_zero_and_missing_distances_separate():
    assert measurements("bsda", {"components": {
        "semantic": {"raw_distance": 0, "unmeasurable": False},
        "instruction": {"raw_distance": None, "unmeasurable": True},
        "safety": {"raw_distance": .5, "unmeasurable": True},
    }}) == [{"label": "semantic raw distance", "value": 0, "unit": "distance"}]


def test_diagnostics_do_not_turn_evidence_into_scores():
    assert measurements("draa", {"features": [{}, {}], "risk_score": None}) == [
        {"label": "Evidence features", "value": 2, "unit": "count"}]
    assert measurements("pri", {"cells": [], "coverage": {"requested_categories": ["a", "b"], "observed_categories": ["a"]}})[-1]["value"] == 1


def test_statistics_reject_non_numeric_and_non_finite_values():
    result = measurements("statistics", {"values": {"mean": 12, "median": 0, "missing": None, "boolean": True, "infinite": float("inf")}, "n_valid": 2})
    assert [item["value"] for item in result] == [12, 0, 2]


def test_recovery_alias_projection_and_negative_sequence_effect():
    assert measurements("rc", {"rc_auc_raw": -.5})[0]["value"] == -.5
    assert measurements("saea", {"per_step": [{"context_effect": -.2}]})[0]["value"] == -.2


def test_statistic_units_preserve_latency_and_squared_variance():
    result = measurements("statistics", {"values": {"mean": 12, "sample_variance": 4}}, units="ms")
    assert [item["unit"] for item in result] == ["ms", "ms squared"]


def test_profile_identifies_source_without_exposing_private_provenance():
    from sqlalchemy.orm import Session
    from apps.api.metric_projection import project_profiles
    from core.persistence.database import Base, make_engine
    from core.persistence.models import ScientificRecordEntity

    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(ScientificRecordEntity(id="fixture-record", family="draa", schema_version="v1",
            scope="run", owner_id="fixture-run", status="evidence_only",
            payload={"features": [], "risk_score": None}, provenance={"api_key": "test-only"}))
        session.commit()
        profiles = project_profiles(session, ["fixture-run"], [])
        profile = next(row for row in profiles if row["family"] == "draa")
        assert profile["source_record_id"] == "fixture-record"
        assert profile["value"] is None
        assert "provenance" not in profile
        assert next(row for row in profiles if row["family"] == "pri")["source_record_id"] is None
    engine.dispose()


def test_missing_embeddings_do_not_present_legacy_defaults_as_measurements():
    from sqlalchemy.orm import Session
    from apps.api.metric_projection import project_profiles
    from core.persistence.database import Base, make_engine
    from core.persistence.models import ScientificRecordEntity

    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        record = ScientificRecordEntity(id="legacy-dqi", family="dqi", schema_version="v1",
            scope="DATASET_VERSION", owner_id="dataset", status="computed",
            payload={"score": .5, "components": {"novelty": 0, "coverage": 1}},
            provenance={"embeddings_supplied": False})
        session.add(record)
        session.commit()
        profile = next(row for row in project_profiles(session, ["dataset"], []) if row["family"] == "dqi")
        assert profile["value"] is None
        assert profile["components"]["novelty"] is None
        assert profile["measurements"] == [{"label": "coverage", "value": 1, "unit": "ratio", "sample_count": 1}]
        assert record.payload == {"score": .5, "components": {"novelty": 0, "coverage": 1}}
    engine.dispose()
