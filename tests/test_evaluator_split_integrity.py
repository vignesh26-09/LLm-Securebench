import pytest

from core.evaluation.judge_calibration import JudgeCalibrationPair, build_judge_calibration_artifact
from core.evaluation.split_integrity import validate_evaluator_splits


def test_related_prompts_cannot_cross_splits():
    rows = [{"evaluation_id": "a", "related_group_id": "same", "split": "development"},
            {"evaluation_id": "b", "related_group_id": "same", "split": "test"}]
    with pytest.raises(ValueError, match="related groups cross"):
        validate_evaluator_splits(rows)


def test_disjoint_grouped_splits_are_counted():
    rows = [{"evaluation_id": "a", "related_group_id": "g1", "split": "development"},
            {"evaluation_id": "b", "related_group_id": "g2", "split": "test"}]
    counts = validate_evaluator_splits(rows)
    assert counts["development"] == 1
    assert counts["test"] == 1


def test_calibration_specificity_and_balanced_accuracy():
    pairs = [JudgeCalibrationPair("tp", True, True),
             JudgeCalibrationPair("fn", True, False),
             JudgeCalibrationPair("tn", False, False),
             JudgeCalibrationPair("fp", False, True)]
    artifact = build_judge_calibration_artifact(pairs, artifact_id="synthetic", dataset="fixture",
        dataset_revision="fixture", dataset_hash="fixture", judge_provider="fixture",
        judge_model="fixture", judge_model_version=None, judge_prompt_version="v1",
        rubric_version="v1", label_mapping={}, human_label_source="synthetic_fixture",
        software_version=None, bootstrap_resamples=10)
    assert artifact.specificity == 0.5
    assert artifact.balanced_accuracy == 0.5
    assert artifact.validation_status == "not_validated"
