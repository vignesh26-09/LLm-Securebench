"""Publication chart exports from explicitly real persisted evidence only.

No generator creates an empty figure.  Fixtures and synthetic records are
rejected before aggregation; insufficient evidence returns structured status.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sqlalchemy import select

from core.persistence.models import ScientificRecordEntity


CHART_TYPES = frozenset({"judge_calibration", "bsda_distribution", "recovery_distribution",
                         "saea_deviation", "applicability_summary"})


@dataclass(frozen=True, slots=True)
class ChartResult:
    status: str
    requested: str
    record_count: int
    minimum_required: int
    excluded_counts: Mapping[str, int]
    data: Sequence[Mapping[str, object]]
    svg_path: str | None = None
    png_path: str | None = None
    csv_path: str | None = None
    json_path: str | None = None
    reason: str | None = None


def generate_chart(session, chart_type: str, *, output_dir: Path,
                   model: str | None = None, dataset: str | None = None,
                   category: str | None = None) -> ChartResult:
    if chart_type not in CHART_TYPES:
        raise ValueError("unsupported_chart_type")
    filters = {"model": model, "dataset": dataset, "category": category}
    makers: Mapping[str, Callable] = {
        "judge_calibration": _judge_calibration,
        "bsda_distribution": _bsda_distribution,
        "recovery_distribution": _recovery_distribution,
        "saea_deviation": _saea_deviation,
        "applicability_summary": _applicability_summary,
    }
    return makers[chart_type](session, output_dir, filters)


def _judge_calibration(session, output_dir, filters):
    records = _real_records(session, "judge_calibration", filters)
    if len(records) != 1:
        return _insufficient("judge_calibration", len(records), 1, {}, "exactly_one_real_calibration_artifact_required")
    payload = records[0].payload
    matrix = payload.get("confusion_matrix", {})
    values = {key: matrix.get(key) for key in ("tp", "fp", "fn", "tn")}
    if any(not isinstance(value, int) for value in values.values()):
        return _insufficient("judge_calibration", 0, 1, {}, "confusion_matrix_missing_or_invalid")
    row = {"artifact_id": records[0].id, **values, "coverage": payload.get("coverage"),
           "raw_agreement": payload.get("agreement", payload.get("raw_agreement")),
           "cohen_kappa": payload.get("cohen_kappa"), "usable_n": payload.get("usable_sample_size"),
           "source_n": payload.get("sample_size")}
    if not all(isinstance(row[key], (int, float)) for key in ("coverage", "raw_agreement", "cohen_kappa")):
        return _insufficient("judge_calibration", 0, 1, {}, "calibration_summary_missing_or_invalid")
    figure, axis = plt.subplots(figsize=(6.2, 5.3))
    grid = [[values["tn"], values["fn"]], [values["fp"], values["tp"]]]
    image = axis.imshow(grid, cmap="Blues")
    for row_index, entries in enumerate(grid):
        for column_index, value in enumerate(entries):
            axis.text(column_index, row_index, str(value), ha="center", va="center", fontsize=16, fontweight="bold")
    axis.set_xticks((0, 1), ("Human negative", "Human positive"))
    axis.set_yticks((0, 1), ("Judge negative", "Judge positive"))
    axis.set_title("JailbreakBench judge calibration")
    figure.colorbar(image, ax=axis, label="Count")
    axis.set_xlabel(f"Coverage {row['coverage']:.1%}   Agreement {row['raw_agreement']:.1%}   κ={row['cohen_kappa']:.3f}")
    return _export("judge_calibration", output_dir, filters, [row], figure, {})


def _bsda_distribution(session, output_dir, filters):
    records = _real_records(session, "bsda", filters)
    rows = []
    excluded = {"missing_component": 0}
    for record in records:
        payload = record.payload
        components = payload.get("components", payload)
        for name in ("D_sem", "D_safety", "D_instr", "D_struct"):
            value = components.get(name, components.get(name.lower())) if isinstance(components, Mapping) else None
            if isinstance(value, (int, float)):
                rows.append({"record_id": record.id, "model": _identity(record, "model"), "component": name, "value": value})
            else:
                excluded["missing_component"] += 1
    if len(records) < 5 or len(rows) < 5:
        return _insufficient("bsda_distribution", len(records), 5, excluded, "fewer_than_five_real_component_values")
    figure, axis = plt.subplots(figsize=(7, 4.5))
    groups = [[row["value"] for row in rows if row["component"] == name] for name in ("D_sem", "D_safety", "D_instr", "D_struct")]
    axis.boxplot(groups, tick_labels=("D_sem", "D_safety", "D_instr", "D_struct"), showmeans=True)
    axis.set_ylabel("BSDA component value")
    axis.set_title("BSDA component distribution")
    return _export("bsda_distribution", output_dir, filters, rows, figure, excluded, source_record_count=len(records))


def _recovery_distribution(session, output_dir, filters):
    records = _real_records(session, "recovery", filters)
    rows, excluded = [], {"not_applicable": 0, "uncalibrated": 0, "blocked": 0, "missing_rc_auc": 0}
    for record in records:
        status = str(record.status or record.payload.get("status", "unknown"))
        value = record.payload.get("rc_auc_raw", record.payload.get("auc"))
        if status not in {"applicable", "computed"}:
            excluded[_excluded_bucket(status)] += 1
        elif isinstance(value, (int, float)):
            rows.append({"record_id": record.id, "model": _identity(record, "model"), "rc_auc": value})
        else:
            excluded["missing_rc_auc"] += 1
    if len(rows) < 5:
        return _insufficient("recovery_distribution", len(records), 5, excluded, "fewer_than_five_applicable_real_rc_values")
    figure, axis = plt.subplots(figsize=(7, 4.5)); axis.boxplot([row["rc_auc"] for row in rows], showmeans=True)
    axis.set_xticks((1,), ("RC-AUC",)); axis.set_ylabel("Raw recovery AUC"); axis.set_title("Recovery capability distribution")
    return _export("recovery_distribution", output_dir, filters, rows, figure, excluded, source_record_count=len(records))


def _saea_deviation(session, output_dir, filters):
    records = _real_records(session, "saea", filters)
    rows, excluded = [], {"undefined_or_blocked": 0, "missing_delta": 0}
    for record in records:
        for step in record.payload.get("per_step", ()):
            delta, isolated = step.get("delta"), step.get("isolated_delta")
            if step.get("status") != "applicable":
                excluded["undefined_or_blocked"] += 1
            elif isinstance(delta, (int, float)) and isinstance(isolated, (int, float)):
                rows.append({"record_id": record.id, "model": _identity(record, "model"),
                             "position": step.get("position"), "delta": delta, "isolated_delta": isolated,
                             "deviation": delta - isolated})
            else:
                excluded["missing_delta"] += 1
    if len(rows) < 5:
        return _insufficient("saea_deviation", len(records), 5, excluded, "fewer_than_five_applicable_real_saea_deltas")
    figure, axis = plt.subplots(figsize=(6, 5)); axis.scatter([row["isolated_delta"] for row in rows], [row["delta"] for row in rows])
    axis.set_xlabel("Isolated vulnerability V_iso(Aᵢ)"); axis.set_ylabel("Sequential Δᵢ"); axis.set_title("Sequential versus isolated deviation")
    return _export("saea_deviation", output_dir, filters, rows, figure, excluded, source_record_count=len(records))


def _applicability_summary(session, output_dir, filters):
    records = []
    for family in ("bsda", "recovery", "saea"):
        records.extend(_real_records(session, family, filters))
    grouped: dict[tuple[str, str, str], int] = {}
    for record in records:
        key = (record.family, _identity(record, "model"), _summary_status(record.status or record.payload.get("status")))
        grouped[key] = grouped.get(key, 0) + 1
    rows = [{"metric": metric, "model": model, "status": status, "count": count}
            for (metric, model, status), count in sorted(grouped.items())]
    if not rows:
        return _insufficient("applicability_summary", 0, 1, {}, "no_real_metric_records")
    figure, axis = plt.subplots(figsize=(8, 4.5))
    labels = [f"{row['metric']}\n{row['model']}\n{row['status']}" for row in rows]
    axis.bar(range(len(rows)), [row["count"] for row in rows]); axis.set_xticks(range(len(rows)), labels, rotation=40, ha="right")
    axis.set_ylabel("Record count"); axis.set_title("Metric applicability and missingness")
    return _export("applicability_summary", output_dir, filters, rows, figure, {}, source_record_count=len(records))


def _real_records(session, family, filters):
    rows = session.scalars(select(ScientificRecordEntity).where(ScientificRecordEntity.family == family)).all()
    return [row for row in rows if _is_real(row) and _matches(row, filters)]


def _is_real(record) -> bool:
    provenance = record.provenance or {}
    return (provenance.get("data_origin") == "real_persisted"
            and provenance.get("reporting_class") in {"phase1_scientific", "external_calibration"}
            and not provenance.get("fixture", False) and not provenance.get("synthetic", False))


def _matches(record, filters):
    payload = record.payload or {}; provenance = record.provenance or {}
    for key, value in filters.items():
        if value and payload.get(key, provenance.get(key)) != value:
            return False
    return True


def _identity(record, key):
    return str((record.payload or {}).get(key, (record.provenance or {}).get(key, "unspecified")))


def _excluded_bucket(status):
    if status in {"not_applicable", "unavailable"}: return "not_applicable"
    if "calibrat" in status or status == "uncalibrated": return "uncalibrated"
    return "blocked"


def _summary_status(status):
    if status in {"applicable", "computed"}: return "computed"
    return _excluded_bucket(str(status))


def _insufficient(requested, count, minimum, excluded, reason):
    return ChartResult("insufficient_data", requested, count, minimum, excluded, (), reason=reason)


def _export(chart_type, output_dir, filters, rows, figure, excluded, *, source_record_count=None):
    token = hashlib.sha256(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = output_dir / f"{chart_type}_{stamp}_{token}"
    output_dir.mkdir(parents=True, exist_ok=True)
    svg, png, csv_path, json_path = (prefix.with_suffix(suffix) for suffix in (".svg", ".png", ".csv", ".json"))
    figure.tight_layout(); figure.savefig(svg, format="svg", dpi=300); figure.savefig(png, format="png", dpi=300); plt.close(figure)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0])); writer.writeheader(); writer.writerows(rows)
    json_path.write_text(json.dumps({"chart_type": chart_type, "filters": filters, "data": rows,
                                     "excluded_counts": excluded}, indent=2), encoding="utf-8")
    return ChartResult("ready", chart_type, source_record_count if source_record_count is not None else len(rows), 1, excluded, rows,
                       str(svg), str(png), str(csv_path), str(json_path))
