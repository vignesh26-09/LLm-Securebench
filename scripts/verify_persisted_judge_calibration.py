"""Recompute stored JBB comparison diagnostics without calling or tuning a judge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root: Path = ROOT) -> dict[str, object]:
    result = json.loads((root / "experiments/jailbreakbench-validation/results.json").read_text(encoding="utf-8"))
    artifact = json.loads((root / "experiments/jailbreakbench-validation/calibration_artifact_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "data/external/jailbreakbench_judge_comparison_b2b462fd.manifest.json").read_text(encoding="utf-8"))
    source = root / manifest["local_file"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest["sha256"] or digest != artifact["dataset_hash"] or digest != result["source"]["sha256"]:
        raise ValueError("JailbreakBench source checksum mismatch")
    records = result["records"]
    pairs = [(row["prediction"], row["human_majority"]) for row in records if row["prediction"] is not None]
    if not pairs:
        raise ValueError("stored judge comparison has no usable records")
    n = len(pairs)
    matrix = {"tn": sum(p == 0 and h == 0 for p, h in pairs),
              "fp": sum(p == 1 and h == 0 for p, h in pairs),
              "fn": sum(p == 0 and h == 1 for p, h in pairs),
              "tp": sum(p == 1 and h == 1 for p, h in pairs)}
    agreement = (matrix["tn"] + matrix["tp"]) / n
    human_positive = (matrix["fn"] + matrix["tp"]) / n
    judge_positive = (matrix["fp"] + matrix["tp"]) / n
    expected = human_positive * judge_positive + (1 - human_positive) * (1 - judge_positive)
    kappa = (agreement - expected) / (1 - expected) if expected < 1 else None
    coverage = n / len(records)
    if (len(records) != manifest["record_count"] or len(records) != artifact["sample_size"]
            or n != artifact["usable_sample_size"] or matrix != artifact["confusion_matrix"]
            or any(abs(actual - stored) > 1e-12 for actual, stored in (
                (coverage, artifact["coverage"]), (agreement, artifact["agreement"]),
                (kappa, artifact["cohen_kappa"]), (coverage, result["coverage"]),
                (agreement, result["agreement"]["accuracy"]),
                (kappa, result["agreement"]["cohen_kappa"])))):
        raise ValueError("stored judge calibration does not reproduce")
    return {"source_n": len(records), "usable_n": n, "coverage": coverage,
            "raw_agreement": agreement, "cohen_kappa": kappa,
            "confusion_matrix": matrix, "source_sha256": digest,
            "status": "verified_from_persisted_artifacts"}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
