"""Analysis export for a paper trace; descriptive only unless prerequisites exist."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.statistics.correlation import spearman
from core.statistics.descriptive import summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    trace = json.loads(Path(args.input).read_text(encoding="utf-8"))
    layer1 = [value["aggregate_score"] for value in trace["layer1"].values()]
    latencies = [value["latency_ms"] for value in trace["responses"].values() if isinstance(value, dict)]
    bsda = trace["bsda"]["components"]
    bsda_components = [component["raw_distance"] for component in bsda.values() if component["raw_distance"] is not None]
    analysis = {
        "trace_id": trace["trace_id"],
        "scientifically_validated": False,
        "descriptive": {
            "layer1_aggregate": asdict(summarize(layer1)),
            "latency_ms": asdict(summarize(latencies)),
            "bsda_components": asdict(summarize(bsda_components)),
        },
        "correlation": {
            "layer1_vs_latency_spearman": asdict(spearman(layer1, latencies, pairing_declared=True)),
        },
        "blocked": {
            "asr": trace.get("asr", {"status": "insufficient_data", "reason": "requires explicit approved attack-outcome labels and denominator policy"}),
            "ml": "requires independent labels and leakage-reviewed feature schema",
            "confirmatory_claims": "require preregistered plan and scientific review",
        },
    }
    output = Path(args.output) if args.output else Path(args.input).with_name("fixture_analysis.json")
    output.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "trace_id": trace["trace_id"], "scientifically_validated": False}))


if __name__ == "__main__":
    main()
