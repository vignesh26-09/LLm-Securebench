"""Publication chart exports from explicitly real persisted evidence only.

No generator creates an empty figure.  Fixtures and synthetic records are
rejected before aggregation; insufficient evidence returns structured status.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
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
                         "saea_deviation", "applicability_summary", "recovery_trajectory",
                         "saea_trajectory", "latency_per_turn"})


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
        "recovery_trajectory": _recovery_trajectory,
        "saea_trajectory": _saea_trajectory,
        "latency_per_turn": _latency_per_turn,
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
        for name, native_name in (("D_sem", "semantic"), ("D_safety", "safety"),
                                  ("D_instr", "instruction"), ("D_struct", "structural")):
            value = components.get(name, components.get(name.lower(), components.get(native_name))) if isinstance(components, Mapping) else None
            if isinstance(value, Mapping):
                value = value.get("raw_distance")
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
    records = _real_records(session, "rc", filters) + _real_records(session, "recovery", filters)
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


def _line_records(session, families, filters):
    """Keep the publication gate; count rejected records, never promote evidence.

    Counts ending in _records are source records, while _points are candidate
    positions. Record rejection reasons can overlap (for example engineering
    provenance AND uncalibrated status). Two valid positions in the SAME series are an engineering
    rendering minimum, not a scientific sample-size requirement.
    """
    candidates = session.scalars(select(ScientificRecordEntity).where(
        ScientificRecordEntity.family.in_(families))).all()
    excluded = {"provenance_rejected_records": 0, "not_applicable_records": 0,
                "uncalibrated_records": 0, "blocked_records": 0,
                "invalid_points": 0, "ineligible_points": 0,
                "not_applicable_points": 0, "uncalibrated_points": 0, "blocked_points": 0,
                "short_series_points": 0}
    records = []
    matched_count = 0
    for record in candidates:
        if not _matches(record, filters):
            continue
        matched_count += 1
        provenance_rejected = not _is_real(record) or (record.provenance or {}).get("synthetic_fixture", False)
        if provenance_rejected:
            excluded["provenance_rejected_records"] += 1
        statuses = {str(value) for value in (record.status, record.payload.get("status"))
                    if value is not None}
        status_rejected = not statuses or not statuses <= {"computed", "applicable", "completed"}
        if status_rejected:
            bucket = ("uncalibrated_records" if any("calibrat" in s for s in statuses)
                      else "not_applicable_records" if "not_applicable" in statuses
                      else "blocked_records")
            excluded[bucket] += 1
        if provenance_rejected or status_rejected:
            continue
        records.append(record)
    return records, matched_count, excluded


def _finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _position(value, *, minimum=1):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _recovery_trajectory(session, output_dir, filters):
    records, count, excluded = _line_records(session, ("rc", "recovery"), filters)
    rows = []
    for record in records:
        for item in record.payload.get("recovery_deltas", ()):
            if (not isinstance(item, (list, tuple)) or len(item) != 2
                    or not _position(item[0]) or not _finite_number(item[1])):
                excluded["invalid_points"] += 1
                continue
            rows.append({"record_id": record.id, "series_id": record.id,
                         "position": item[0], "deviation": item[1]})
    return _line_export("recovery_trajectory", output_dir, filters, rows, count, excluded,
                        (("deviation", "Deviation from baseline"),),
                        "Recovery turn", "Normalized Euclidean distance")


def _saea_trajectory(session, output_dir, filters):
    records, count, excluded = _line_records(session, ("saea",), filters)
    rows = []
    for record in records:
        for step in record.payload.get("per_step", ()):
            if not isinstance(step, Mapping) or step.get("status") != "applicable":
                excluded["ineligible_points"] += 1
                bucket = _excluded_bucket(str(step.get("status"))) if isinstance(step, Mapping) else "blocked"
                excluded[f"{bucket}_points"] += 1
                continue
            if (not _position(step.get("position"))
                    or not all(_finite_number(step.get(k)) for k in ("delta", "isolated_delta"))):
                excluded["invalid_points"] += 1
                continue
            rows.append({"record_id": record.id, "series_id": record.id,
                         "position": step["position"], "delta": step["delta"],
                         "isolated_delta": step["isolated_delta"]})
    return _line_export("saea_trajectory", output_dir, filters, rows, count, excluded,
                        (("delta", "Sequential delta"), ("isolated_delta", "Isolated V_iso")),
                        "Attack position", "Normalized Euclidean distance")


def _latency_per_turn(session, output_dir, filters):
    records, count, excluded = _line_records(session, ("experimental_condition",), filters)
    rows = []
    for record in records:
        payload = record.payload
        metadata = payload.get("provider_metadata")
        latency = metadata.get("client_elapsed_latency_ms") if isinstance(metadata, Mapping) else None
        if not _position(payload.get("turn_index"), minimum=0) or not _finite_number(latency) or latency < 0:
            excluded["invalid_points"] += 1
            continue
        # Conversation boundaries prevent connecting isolated controls or runs.
        conversation = payload.get("conversation_id")
        run = payload.get("run_id")
        if not conversation or not run:
            excluded["invalid_points"] += 1
            continue
        rows.append({"record_id": record.id, "series_id": f"{run}:{conversation}",
                     "position": payload["turn_index"], "latency_ms": latency})
    return _line_export("latency_per_turn", output_dir, filters, rows, count, excluded,
                        (("latency_ms", "Client elapsed latency"),), "Conversation turn", "Milliseconds")


def _line_export(chart_type, output_dir, filters, rows, count, excluded, measures, xlabel, ylabel):
    groups = {}
    for row in rows:
        groups.setdefault(row["series_id"], []).append(row)
    retained = {}
    for identity, points in groups.items():
        positions = [point["position"] for point in points]
        if len(positions) != len(set(positions)):
            excluded["invalid_points"] += len(points)
        elif len(points) < 2:
            excluded["short_series_points"] += len(points)
        else:
            retained[identity] = sorted(points, key=lambda point: point["position"])
    if not retained:
        return _insufficient(chart_type, count, 2, excluded,
                             "at_least_two_eligible_positions_in_one_series_required")
    figure, axis = plt.subplots(figsize=(8, 4.8))
    exported = []
    for identity, points in sorted(retained.items()):
        exported.extend(points)
        for field, label in measures:
            x, y, previous = [], [], None
            for point in points:
                if previous is not None and point["position"] != previous + 1:
                    x.append(math.nan); y.append(math.nan)
                x.append(point["position"]); y.append(point[field]); previous = point["position"]
            axis.plot(x, y, marker="o", label=f"{identity}: {label}")
    axis.set_xlabel(xlabel); axis.set_ylabel(ylabel)
    axis.set_title(chart_type.replace("_", " ").capitalize())
    if len(retained) * len(measures) <= 8:
        axis.legend(fontsize="x-small")
    result = _export(chart_type, output_dir, filters, exported, figure, excluded,
                     source_record_count=count)
    # The export helper's older default is one; these lines require two positions.
    from dataclasses import replace
    return replace(result, minimum_required=2)


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
