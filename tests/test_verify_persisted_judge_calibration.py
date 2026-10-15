from pathlib import Path

from scripts.verify_persisted_judge_calibration import verify


def test_real_persisted_calibration_reproduces_without_live_judge():
    root = Path(__file__).resolve().parents[1]
    result = verify(root)
    assert result["source_n"] == 300
    assert result["usable_n"] == 295
    assert result["confusion_matrix"] == {"tn": 51, "fp": 135, "fn": 1, "tp": 108}
    assert round(result["cohen_kappa"], 3) == 0.211
