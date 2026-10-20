from core.statistics.paired import PairedValue, grouped_paired_analyses


def test_grouped_pairs_preserve_exclusion_and_missingness_rules():
    values = (
        PairedValue("a1", 0.0, 2.0, groups={"model": "a"}),
        PairedValue("a2", 4.0, 8.0, groups={"model": "a"}),
        PairedValue("excluded-a", 100.0, 1000.0, groups={"model": "a"}, exclusion_reason="failed evaluation"),
        PairedValue("missing-a", None, 500.0, groups={"model": "a"}),
        PairedValue("excluded-b", 5.0, 9.0, groups={"model": "b"}, exclusion_reason="identity mismatch"),
        PairedValue("missing-b", 7.0, None, groups={"model": "b"}),
    )
    results = grouped_paired_analyses(
        values, group="model", sample_definition="synthetic grouped pairs", seed=42, resamples=100,
    )

    assert set(results) == {"a", "b"}
    a, b = results["a"], results["b"]
    assert a.grouping_variables == {"model": "a"}
    assert a.missingness == {"left_missing": 1, "right_missing": 0, "explicitly_excluded": 1}
    assert a.n == 2
    assert a.statistic == {"mean_left": 2.0, "mean_right": 5.0, "mean_difference": 3.0}
    assert a.status == "computed"
    assert b.grouping_variables == {"model": "b"}
    assert b.missingness == {"left_missing": 0, "right_missing": 1, "explicitly_excluded": 1}
    assert b.n == 0
    assert all(value is None for value in b.statistic.values())
    assert b.confidence_interval is None
    assert b.status == "unsupported"
    assert b.reason == "no_complete_pairs"
