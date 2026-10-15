"""Compare stored binary judge outputs on the same source-native JBB records.

No model is invoked. Additional evaluator predictions require a predeclared
binary mapping and a SHA-256-pinned JSON file; scores are never auto-thresholded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.evaluation.evaluator_comparison import compare_binary_evaluators
from scripts.verify_persisted_judge_calibration import verify

SOURCE_COLUMNS = ("harmbench_cf", "gpt4_cf", "llamaguard2_cf", "llama3_cf")


def _binary(value):
    if type(value) is bool:
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    if type(value) is str and value in ("0", "1"):
        return value == "1"
    if value is None:
        return None
    raise ValueError("evaluator prediction must be an explicit binary label or null")


def load_rows(root: Path, *, extra: list[dict] | None = None) -> tuple[list[dict], list[str], dict]:
    verified = verify(root)
    source_path = root / "data/external/jailbreakbench_judge_comparison_b2b462fd.csv"
    with source_path.open(encoding="utf-8", newline="") as handle:
        source = list(csv.DictReader(handle))
    result = json.loads((root / "experiments/jailbreakbench-validation/results.json").read_text(encoding="utf-8"))
    predictions = {str(item["index"]): item for item in result["records"]}
    if len(predictions) != len(source):
        raise ValueError("stored judge record IDs are duplicated or missing")
    external = {}
    for config in extra or []:
        name = config.get("name")
        path = Path(config.get("path", ""))
        if not isinstance(name, str) or not name or name in SOURCE_COLUMNS or name == "gemma3_4b_fixed_mapping" or name in external:
            raise ValueError("external evaluator name is invalid or duplicated")
        if not all(isinstance(config.get(field), str) and config[field] for field in
                   ("rubric_version", "model_version", "positive_label_rule", "sha256")):
            raise ValueError("external evaluator requires versioned rubric/model/mapping and checksum")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != config["sha256"]:
            raise ValueError("external prediction file missing or checksum mismatch")
        values = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(values, list) or len(values) != len(source):
            raise ValueError("external evaluator predictions must cover all source IDs")
        joined = {}
        for item in values:
            key = str(item.get("evaluation_id", ""))
            if not key or key in joined:
                raise ValueError("external evaluator IDs missing or duplicated")
            joined[key] = _binary(item.get("prediction"))
        if set(joined) != set(predictions):
            raise ValueError("external evaluator IDs differ from source IDs")
        external[name] = joined
    names = ["gemma3_4b_fixed_mapping", *SOURCE_COLUMNS, *external]
    rows = []
    for item in source:
        key = str(item["Index"])
        if key not in predictions or _binary(item["human_majority"]) is None:
            raise ValueError("source/judge identity or reference label is invalid")
        prediction = _binary(predictions[key]["prediction"])
        # Related prompts sharing a goal are one bootstrap cluster. The goal is
        # hashed so no harmful source text enters the aggregate report.
        group_id = hashlib.sha256(item["goal"].encode("utf-8")).hexdigest()
        rows.append({"evaluation_id": key, "human_label": _binary(item["human_majority"]),
                     "group_id": group_id,
                     "predictions": {"gemma3_4b_fixed_mapping": prediction,
                                     **{name: _binary(item[name]) for name in SOURCE_COLUMNS},
                                     **{name: joined[key] for name, joined in external.items()}}})
    return rows, names, verified


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extra-config", type=Path,
                        help="JSON list of pinned external binary-prediction files")
    parser.add_argument("--bootstrap-resamples", type=int, default=1000)
    args = parser.parse_args()
    configs = json.loads(args.extra_config.read_text(encoding="utf-8")) if args.extra_config else []
    if not isinstance(configs, list):
        raise SystemExit("extra-config must be a JSON list")
    rows, names, verified = load_rows(ROOT, extra=configs)
    comparison = compare_binary_evaluators(rows, evaluator_names=names,
        bootstrap_resamples=args.bootstrap_resamples)
    report = {"schema_version": "evaluator-comparison-v1", "source": verified,
              "reference_label": "JailbreakBench human_majority; positive=1",
              "evaluators": {"gemma3_4b_fixed_mapping": {
                  "origin": "persisted local Gemma 3:4B safety_stance score < 0.5",
                  "rubric_difference": "Safety-stance score mapped to jailbreak outcome; not the official JBB rubric"},
                  **{name: {"origin": "JailbreakBench judge_comparison source column",
                            "rubric_difference": "Source-native binary jailbreak classifier"} for name in SOURCE_COLUMNS},
                  **{item["name"]: {"origin": "pinned external prediction file",
                                     "rubric_version": item["rubric_version"],
                                     "model_version": item["model_version"],
                                     "positive_label_rule": item["positive_label_rule"],
                                     "sha256": item["sha256"]} for item in configs}},
              "comparison": comparison,
              "limitations": ["No declared held-out split in the historical source artifact",
                              "Common-case comparison is descriptive, not a newly run evaluator benchmark",
                              "No attack-family field exists in the source CSV; subgroup status unavailable",
                              "Goal-hash cluster bootstrap is exploratory and does not account for every dependence"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"output": str(args.output), "status": comparison["status"],
                      "common_n": comparison["common_n"], "evaluator_count": len(names)}))


if __name__ == "__main__":
    main()
