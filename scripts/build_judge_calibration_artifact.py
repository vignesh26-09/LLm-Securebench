"""Build a self-contained versioned artifact from persisted JBB comparison rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.evaluation.judge_calibration import JudgeCalibrationPair, build_judge_calibration_artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data/external/jailbreakbench_judge_comparison_b2b462fd.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/external/jailbreakbench_judge_comparison_b2b462fd.manifest.json")
    parser.add_argument("--results", type=Path, default=ROOT / "experiments/jailbreakbench-validation/results.json")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/jailbreakbench-validation/calibration_artifact_v1.json")
    parser.add_argument("--judge-model", default="gemma3:4b")
    parser.add_argument("--judge-model-version")
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=2026)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    digest = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if digest != manifest["sha256"] or digest != results["source"]["sha256"]:
        raise SystemExit("source checksum differs from persisted provenance")
    with args.source.open(encoding="utf-8", newline="") as handle:
        source = {row["Index"]: row for row in csv.DictReader(handle)}
    pairs = []
    for row in results["records"]:
        source_row = source[str(row["index"])]
        if int(source_row["human_majority"]) != int(row["human_majority"]):
            raise SystemExit(f"human label mismatch at index {row['index']}")
        prediction = row.get("prediction")
        pairs.append(JudgeCalibrationPair(
            str(row["index"]), bool(int(row["human_majority"])),
            None if prediction is None else bool(int(prediction)), None))
    captured_config = results.get("judge_configuration", {})
    captured_digest = next((row.get("generation_metadata", {}).get("model_digest")
                            for row in results["records"]
                            if row.get("generation_metadata", {}).get("model_digest")), None)
    artifact = build_judge_calibration_artifact(
        pairs, artifact_id="jbb-gemma-fixed-mapping-v1",
        dataset=manifest["source_name"], dataset_revision=manifest["dataset_revision"],
        dataset_hash=digest, judge_provider="ollama-local-judge",
        judge_model=captured_config.get("model", args.judge_model),
        judge_model_version=captured_digest or args.judge_model_version or captured_config.get("model_version"),
        judge_prompt_version=captured_config.get("prompt_version", "jbb-calibration-prompt-v1"),
        rubric_version=captured_config.get("rubric_version", "jbb-calibration-rubric-v1"),
        label_mapping={"human_positive": 1, "judge_positive_rule": results["protocol"]["prediction_rule"],
                       "threshold": results["protocol"]["threshold"]},
        human_label_source="JailbreakBench human_majority",
        software_version=_git_commit(), bootstrap_resamples=args.bootstrap_resamples,
        bootstrap_seed=args.bootstrap_seed,
        provenance={"source_manifest": str(args.manifest.relative_to(ROOT)),
                    "comparison_results": str(args.results.relative_to(ROOT)),
                    "source_csv": str(args.source.relative_to(ROOT)),
                    "judge_model_version_reason": None if (captured_digest or args.judge_model_version or captured_config.get("model_version")) else "not_present_in_original_results",
                    "judge_configuration": captured_config or None,
                    "bootstrap_assumption": "record-level IID percentile bootstrap; exploratory",
                    "scientifically_validated": False},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(asdict(artifact), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "source_n": artifact.sample_size,
                      "usable_n": artifact.usable_sample_size, "coverage": artifact.coverage,
                      "agreement": artifact.agreement, "cohen_kappa": artifact.cohen_kappa,
                      "validation_status": artifact.validation_status}))


def _git_commit() -> str | None:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


if __name__ == "__main__":
    main()
