import json
import sqlite3
from pathlib import Path


def test_grafana_panels_exclude_other_formulas_and_evidence_classes():
    dashboard = json.loads(
        (Path(__file__).resolve().parents[1] / "grafana/dashboards/securellmbench.json").read_text(encoding="utf-8")
    )
    panels = {panel["id"]: panel for panel in dashboard["panels"]}
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE scientific_records (id TEXT, created_at TEXT, family TEXT, status TEXT, payload TEXT, provenance TEXT)"
    )

    def add(id_: str, formula: str, dataset: str, validated: bool, status: str = "computed") -> None:
        connection.execute(
            "INSERT INTO scientific_records VALUES (?, ?, ?, ?, ?, ?)",
            (
                id_, "2026-09-10 12:00:00", "model_score", status,
                json.dumps({"run_id": id_, "model_name": "test-model", "model_score": 0.75, "formula_version": formula}),
                json.dumps({"dataset_kind": dataset, "scientifically_validated": validated}),
            ),
        )

    add("eligible", "engineering-detector-score-v1", "repository_example", False)
    add("new-formula", "engineering-detector-summary-v2", "repository_example", False)
    add("fixture", "engineering-detector-score-v1", "synthetic_fixture", False)
    add("validated", "engineering-detector-score-v1", "repository_example", True)
    add("unfinished", "engineering-detector-score-v1", "repository_example", False, "blocked")

    assert connection.execute(panels[2]["targets"][0]["queryText"]).fetchone()[0] == 1
    assert connection.execute(panels[5]["targets"][0]["queryText"]).fetchall() == [(1, 75.0)]
    assert len(connection.execute(panels[6]["targets"][0]["queryText"]).fetchall()) == 1
    assert panels[5]["type"] == "xychart"
    assert panels[5]["fieldConfig"]["defaults"]["custom"]["show"] == "points+lines"
    assert panels[7]["type"] == "text" and "targets" not in panels[7]
