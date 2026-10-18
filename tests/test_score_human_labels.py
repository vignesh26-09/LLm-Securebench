import csv

import pytest

from scripts.score_human_labels import score


def test_blinded_scoring_validation_metrics_and_undefined_precision(tmp_path):
    def write(name, rows):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    labels = ["safe", "unsafe", "borderline"] * 10
    sheet = [{"id": f"fake-{i:02d}", "prompt": "Synthetic input", "model_output": "Synthetic response",
              "label": label, "notes": ""} for i, label in enumerate(labels)]
    key = [{"id": row["id"], "model": "synthetic-model", "judge_verdict": ("ambiguous" if label == "borderline" else "pass"),
            "llm_reference": label} for row, label in zip(sheet, labels)]
    sheet[0]["label"] = ""
    write("human_sheet.csv", sheet)
    write("human_key.csv", key)
    with pytest.raises(ValueError, match="fake-00"):
        score(tmp_path)
    assert not (tmp_path / "human_validation_report.md").exists()
    sheet[0]["label"] = "SAFE"
    write("human_sheet.csv", sheet)
    with pytest.raises(ValueError, match="fake-00"):
        score(tmp_path)
    sheet[0]["label"] = "safe"
    write("human_sheet.csv", sheet)
    before = [(tmp_path / name).read_bytes() for name in ("human_sheet.csv", "human_key.csv")]
    result = score(tmp_path)
    assert result["agreement_percent"] == pytest.approx(200 / 3)
    assert result["kappa"] == pytest.approx(.5)
    assert result["ac1"] == pytest.approx(13 / 25)
    assert result["recall"] == .5 and result["precision"] == 1
    assert result["recall_ci95"] == pytest.approx([.2992980082, .7007019918])
    assert result["precision_ci95"] == pytest.approx([.7224672001, 1])
    assert result["human_vs_llm_reference"]["agreement_percent"] == 100
    assert (tmp_path / "human_validation_report.md").read_text().startswith("# Human-validated, n=30 (small sample)")
    assert before == [(tmp_path / name).read_bytes() for name in ("human_sheet.csv", "human_key.csv")]
    for row in key:
        row["judge_verdict"] = "pass"
    write("human_key.csv", key)
    result = score(tmp_path)
    assert result["precision"] is None and result["precision_ci95"] is None
