"""Synthetic arithmetic tests plus a read-only check of real stored JBB rows."""

from pathlib import Path

import pytest

from core.evaluation.evaluator_comparison import compare_binary_evaluators
from core.evaluation.evaluator_eligibility import EvaluatorEligibilityPolicy, assess_evaluator_eligibility
from scripts.compare_judge_evaluators import _binary, load_rows
from scripts.diagnose_judge_errors import diagnose


def _rows():
    return [{"evaluation_id": f"synthetic-{i}", "human_label": human,
             "group_id": f"goal-{i // 2}", "split": "test",
             "predictions": {"a": prediction, "b": True}}
            for i, (human, prediction) in enumerate(((True, True), (True, False),
                                                       (False, True), (False, False)))]


def test_common_case_arithmetic_and_grouped_intervals():
    result = compare_binary_evaluators(_rows(), evaluator_names=["a", "b"],
                                       bootstrap_resamples=40, require_held_out=True)
    assert result["status"] == "held_out_test"
    stats = result["evaluators"]["a"]["common_case"]
    assert stats["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert stats["accuracy"] == stats["specificity"] == stats["balanced_accuracy"] == 0.5
    assert stats["cluster_bootstrap_intervals"] is not None


def test_continuous_scores_cannot_silently_become_binary_predictions():
    with pytest.raises(ValueError, match="explicit binary"):
        _binary(0.0)
    assert _binary(0) is False
    assert _binary(1) is True


def test_common_case_excludes_missing_prediction_without_turning_it_to_failure():
    rows = _rows()
    rows[0]["predictions"]["b"] = None
    result = compare_binary_evaluators(rows, evaluator_names=["a", "b"], bootstrap_resamples=30)
    assert result["common_n"] == 3
    assert result["evaluators"]["a"]["source_coverage_n"] == 4
    assert result["evaluators"]["b"]["source_coverage_n"] == 3


def test_held_out_gate_and_claim_policy():
    rows = _rows()
    rows[0]["split"] = "development"
    with pytest.raises(ValueError, match="held-out"):
        compare_binary_evaluators(rows, evaluator_names=["a"], require_held_out=True)
    exploratory = compare_binary_evaluators(rows, evaluator_names=["a"], bootstrap_resamples=30)
    policy = EvaluatorEligibilityPolicy("synthetic-claim", "synthetic-lock", True, .5, 1, 1)
    assert assess_evaluator_eligibility(exploratory, evaluator_name="a", policy=policy,
                                         independent_human_reference=True)["reason"] == "held_out_test_evidence_required"


def test_claim_specific_policy_can_pass_or_fail_only_after_held_out_review():
    held_out = compare_binary_evaluators(_rows(), evaluator_names=["a"],
        bootstrap_resamples=40, require_held_out=True)
    permissive = EvaluatorEligibilityPolicy("synthetic-claim", "synthetic-lock", True, 1, 1, 1)
    result = assess_evaluator_eligibility(held_out, evaluator_name="a", policy=permissive,
        independent_human_reference=True)
    assert result["status"] == "eligible_for_claim_review"
    strict = EvaluatorEligibilityPolicy("synthetic-claim", "synthetic-lock", True, 1, 0, 0)
    result = assess_evaluator_eligibility(held_out, evaluator_name="a", policy=strict,
        independent_human_reference=True)
    assert result["status"] == "ineligible_for_claim"
    assert "false_positive_uncertainty_exceeds_claim_policy" in result["violations"]
    assert assess_evaluator_eligibility(held_out, evaluator_name="a", policy=permissive,
        independent_human_reference=False)["reason"] == "independent_human_reference_required"


def test_real_jbb_comparison_reuses_same_295_records():
    root = Path(__file__).resolve().parents[1]
    rows, names, verified = load_rows(root)
    result = compare_binary_evaluators(rows, evaluator_names=names, bootstrap_resamples=30)
    assert verified["source_n"] == 300
    assert result["common_n"] == 295
    assert result["evaluators"]["gemma3_4b_fixed_mapping"]["common_case"]["confusion_matrix"] == {
        "tn": 51, "fp": 135, "fn": 1, "tp": 108}
    assert result["status"] == "exploratory_no_declared_test_split"


def test_real_diagnostics_keep_family_unavailable_and_do_not_export_text():
    report, rows = diagnose(Path(__file__).resolve().parents[1])
    assert report["error_groups"]["false_positive"]["n"] == 135
    assert report["attack_family"]["status"] == "unavailable"
    assert "target_response" not in rows[0]
    assert "prompt" not in rows[0]
