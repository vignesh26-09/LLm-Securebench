from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from core.reporting import charts


def record(identifier, family, payload, provenance=None):
    return SimpleNamespace(id=identifier, family=family, payload=payload, status="applicable",
        provenance=provenance if provenance is not None else {
            "data_origin": "real_persisted", "reporting_class": "phase1_scientific",
            "fixture": False, "synthetic": False,
        })


def distribution(records, chart_type):
    session = Mock()
    session.scalars.side_effect = lambda statement: SimpleNamespace(
        all=lambda: [r for r in records if r.family == statement.compile().params["family_1"]])

    def capture(kind, output_dir, filters, rows, figure, excluded, *, source_record_count=None):
        return charts.ChartResult("ready", kind, source_record_count, 1, excluded, tuple(rows))

    with patch.object(charts, "plt") as plot, patch.object(charts, "_export", side_effect=capture) as export:
        plot.subplots.return_value = (Mock(), Mock())
        result = charts.generate_chart(session, chart_type, output_dir=Path("unused-in-memory"))
        if result.status == "insufficient_data":
            export.assert_not_called()
            plot.subplots.assert_not_called()
        return result


def native_payload():
    return {"components": {name: {"raw_distance": value, "normalized": None}
            for name, value in zip(("semantic", "safety", "instruction", "structural"), (.1, .2, .3, .4))}}


def test_native_bsda_components_remain_separate():
    result = distribution([record(str(i), "bsda", native_payload()) for i in range(5)], "bsda_distribution")
    assert result.status == "ready"
    assert len(result.data) == 20
    assert {r["component"] for r in result.data} == {"D_sem", "D_safety", "D_instr", "D_struct"}
    assert {r["value"] for r in result.data} == {.1, .2, .3, .4}


@pytest.mark.parametrize("lowercase", [False, True])
def test_legacy_bsda_components_still_work(lowercase):
    components = {name.lower() if lowercase else name: value
                  for name, value in zip(("D_sem", "D_safety", "D_instr", "D_struct"), (.1, .2, .3, .4))}
    result = distribution([record(str(i), "bsda", {"components": components}) for i in range(5)], "bsda_distribution")
    assert result.status == "ready"
    assert len(result.data) == 20


@pytest.mark.parametrize("families", [("rc",) * 5, ("recovery",) * 5, ("rc", "recovery", "rc", "recovery", "rc")])
def test_native_and_legacy_recovery_families_are_read(families):
    result = distribution([record(str(i), family, {"rc_auc_raw": .2})
                           for i, family in enumerate(families)], "recovery_distribution")
    assert result.status == "ready"
    assert len(result.data) == 5
    assert {r["record_id"] for r in result.data} == {str(i) for i in range(5)}
    assert all(r["rc_auc"] == .2 for r in result.data)


@pytest.mark.parametrize("chart_type,family", [("bsda_distribution", "bsda"), ("recovery_distribution", "rc")])
@pytest.mark.parametrize("rejection", [
    {"reporting_class": "engineering_only"}, {"fixture": True},
    {"synthetic": True}, {"data_origin": "unverified"},
])
def test_publication_provenance_gate_still_rejects_records(chart_type, family, rejection):
    provenance = {"data_origin": "real_persisted", "reporting_class": "phase1_scientific", **rejection}
    payload = native_payload() if family == "bsda" else {"rc_auc_raw": .2}
    result = distribution([record(str(i), family, payload, provenance) for i in range(5)], chart_type)
    assert result.status == "insufficient_data"
    assert not result.data


def test_missing_native_component_is_excluded_not_zero():
    payload = native_payload()
    payload["components"]["semantic"]["raw_distance"] = None
    result = distribution([record(str(i), "bsda", payload) for i in range(5)], "bsda_distribution")
    assert result.status == "ready"
    assert result.excluded_counts["missing_component"] == 5
    assert len(result.data) == 15
    assert all(r["component"] != "D_sem" and r["value"] != 0 for r in result.data)
