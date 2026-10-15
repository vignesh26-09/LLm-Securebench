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
