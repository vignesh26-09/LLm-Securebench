"""Export a factual visual report from the newest persisted run per local model."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "local_metrics_report"
API = "http://127.0.0.1:8000"
BLUE = "#2563eb"
ORANGE = "#ea580c"
GRAY = "#64748b"
GRID = "#e2e8f0"
TEXT = "#0f172a"


def get_json(path: str) -> dict:
    with urlopen(f"{API}{path}", timeout=15) as response:
        return json.load(response)


def style(axis, title: str) -> None:
    axis.set_facecolor("white")
    axis.set_title(title, color=TEXT, fontsize=14, fontweight="bold", pad=14)
    axis.tick_params(colors=GRAY)
    axis.grid(axis="y", color=GRID, linewidth=.8)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#cbd5e1")
    axis.spines["bottom"].set_color("#cbd5e1")


def save(figure, name: str, note: str) -> None:
    figure.patch.set_facecolor("white")
    figure.text(.5, .018, note, ha="center", va="bottom", color=GRAY, fontsize=9)
    figure.tight_layout(rect=(0, .065, 1, 1))
    figure.savefig(OUTPUT / f"{name}.png", dpi=200, facecolor="white", bbox_inches="tight")
    figure.savefig(OUTPUT / f"{name}.svg", facecolor="white", bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    scores = get_json("/model-scores?limit=50&offset=0")["items"]
    newest = []
    seen = set()
    for score in scores:
        if score["model_name"] not in seen:
            seen.add(score["model_name"])
            newest.append(score)
        if len(newest) == 3:
            break
    reports = [get_json(f"/benchmark-runs/{score['run_id']}/report") for score in newest]
    if not reports:
        raise RuntimeError("No persisted benchmark reports are available")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    names = [report["run"]["model_name"] for report in reports]
    metrics = {
        "Detector summary": [report["model_score"]["value"] * 100 for report in reports],
        "Mean threat": [report["model_score"]["mean_threat_score"] * 100 for report in reports],
        "Worst threat": [report["model_score"]["worst_case_threat_score"] * 100 for report in reports],
    }
    figure, axis = plt.subplots(figsize=(8.4, 5.2))
    style(axis, "Latest model metric comparison")
    x = list(range(len(names)))
    width = .22
    for offset, (label, values), color in zip((-.22, 0, .22), metrics.items(), (BLUE, ORANGE, GRAY), strict=True):
        bars = axis.bar([point + offset for point in x], values, width, label=label, color=color)
        axis.bar_label(bars, labels=[f"{value:.1f}%" for value in values], padding=3, fontsize=9, color=TEXT)
    axis.set_xticks(x, names)
    axis.set_ylim(0, 100)
    axis.set_ylabel("Percent", color=GRAY)
    axis.legend(frameon=False)
    save(
        figure,
        "01_metric_comparison",
        "Detector summary: fewer configured heuristic signals. Threat values: detector-derived observations. Higher is not proof of safety.",
    )

    figure, axis = plt.subplots(figsize=(8.4, 5.2))
    style(axis, "Per-case response latency behavior")
    colors = (BLUE, ORANGE, GRAY)
    for report, color in zip(reports, colors, strict=False):
        labels = [item["case_id"] or item["id"] for item in report["cases"]]
        values = [item["latency_ms"] / 1000 if item["latency_ms"] is not None else None for item in report["cases"]]
        mean_seconds = report["execution"]["mean_latency_ms"] / 1000
        axis.plot(labels, values, marker="o", linewidth=2.8, markersize=7,
                  label=f"{report['run']['model_name']} (mean {mean_seconds:.2f}s)", color=color)
    axis.set_ylabel("Seconds", color=GRAY)
    axis.legend(frameon=False)
    save(
        figure,
        "02_latency_behavior",
        "Elapsed response time for each pilot case. Lower is faster; latency does not measure security or response quality.",
    )

    detectors = sorted({item["detector"] for report in reports for item in report["detector_summary"]})
    figure, axis = plt.subplots(figsize=(8.4, 5.2))
    style(axis, "Observed detector signal profile")
    width = .7 / len(reports)
    x = list(range(len(detectors)))
    for index, (report, color) in enumerate(zip(reports, colors, strict=False)):
        lookup = {item["detector"]: item["observed_signal_count"] for item in report["detector_summary"]}
        positions = [point - .35 + width / 2 + index * width for point in x]
        values = [lookup.get(name, 0) for name in detectors]
        bars = axis.bar(positions, values, width, label=report["run"]["model_name"], color=color)
        axis.bar_label(bars, labels=[str(value) if value else "" for value in values], padding=3, fontsize=9, color=TEXT)
    axis.set_xticks(x, detectors)
    axis.set_ylabel("Observed signals", color=GRAY)
    axis.yaxis.get_major_locator().set_params(integer=True)
    axis.legend(frameon=False)
    save(
        figure,
        "03_detector_profile",
        "Count of heuristic signals observed in three responses. A signal is an alert for review, not a confirmed successful attack.",
    )

    generated = datetime.now(timezone.utc).isoformat()
    payload = {"generated_at": generated, "scope": "latest persisted run per model", "reports": reports}
    (OUTPUT / "metrics_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Local model metrics report",
        "",
        f"Generated: `{generated}`",
        "",
        "Scope: newest persisted repository-example pilot run per model. All values are engineering observations, not validated safety rankings.",
        "",
        "| Model | Run | Coverage | Detector summary | Mean threat | Worst threat | Mean latency | Signals |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for report in reports:
        signals = sum(item["observed_signal_count"] for item in report["detector_summary"])
        lines.append(
            f"| {report['run']['model_name']} | `{report['run']['id']}` | {report['execution']['coverage']:.1%} | "
            f"{report['model_score']['value']:.1%} | {report['model_score']['mean_threat_score']:.1%} | "
            f"{report['model_score']['worst_case_threat_score']:.1%} | {report['execution']['mean_latency_ms'] / 1000:.2f}s | {signals} |"
        )
    lines.extend([
        "", "## Plots", "",
        "![Metric comparison](01_metric_comparison.png)", "",
        "![Latency behavior](02_latency_behavior.png)", "",
        "![Detector profile](03_detector_profile.png)", "",
        "The pilot has three repository example cases. Detector signals are observations, not confirmed successful attacks or ground-truth outcomes.",
    ])
    (OUTPUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "models": names, "plots": 3}))


if __name__ == "__main__":
    main()
