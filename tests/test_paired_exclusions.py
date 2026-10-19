from core.statistics.paired import PairedValue, paired_difference_analysis


def test_excluded_and_missing_pairs_do_not_enter_the_paired_sample():
    eligible = (PairedValue("a", 0.0, 2.0), PairedValue("b", 4.0, 8.0))
    values = eligible + (
        PairedValue("excluded", 100.0, 1000.0, exclusion_reason="identity mismatch"),
        PairedValue("missing-left", None, 999.0),
        PairedValue("missing-right", 999.0, None),
        PairedValue("excluded-missing", None, None, exclusion_reason="failed evaluation"),
    )
    result = paired_difference_analysis(values, sample_definition="synthetic pairs", seed=42, resamples=100)
    reference = paired_difference_analysis(eligible, sample_definition="synthetic pairs", seed=42, resamples=100)

    assert result.missingness == {"left_missing": 2, "right_missing": 2, "explicitly_excluded": 2}
    assert result.n == 2
    assert result.statistic == {"mean_left": 2.0, "mean_right": 5.0, "mean_difference": 3.0}
    assert result.effect_size == reference.effect_size
    assert result.confidence_interval == reference.confidence_interval
    assert result.status == reference.status


def test_only_excluded_or_missing_pairs_remain_unavailable():
    values = (
        PairedValue("excluded", 1.0, 2.0, exclusion_reason="failed evaluation"),
        PairedValue("missing", None, 3.0),
    )
    result = paired_difference_analysis(values, sample_definition="synthetic pairs")

    assert result.n == 0
    assert result.missingness["explicitly_excluded"] == 1
    assert result.missingness["left_missing"] == 1
    assert all(value is None for value in result.statistic.values())
    assert result.confidence_interval is None
    assert result.status == "unsupported"
    assert result.reason == "no_complete_pairs"
