"""Verify the Phase 4 batch and write two blank, blinded reviewer forms.

The package is local restricted research material. No human labels are created.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.evaluation.phase5_annotation import audit_annotation_batch, form_csv

DEFAULT_PHASE4 = ROOT / "experiments" / "phase4"
DEFAULT_PACKAGE = ROOT / "experiments" / "phase5" / "restricted_annotation_v2"


def _write_once(path: Path, content: bytes) -> str:
    digest = hashlib.sha256(content).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(f"immutable annotation package file differs: {path}")
    else:
        with path.open("xb") as handle:
            handle.write(content)
    return digest


def prepare(phase4: Path = DEFAULT_PHASE4, package: Path = DEFAULT_PACKAGE) -> dict[str, object]:
    observations = phase4 / "jbb_pilot_run_v1" / "observations"
    objectives = phase4 / "jbb_annotation_objectives_v1.json"
    candidates = phase4 / "restricted_annotation" / "candidates_v1.json"
    public = phase4 / "restricted_annotation" / "blinded_batch_v1.json"
    private = phase4 / "restricted_annotation" / "private_join_map_v1.json"
    audit = audit_annotation_batch(observations_dir=observations, objectives_path=objectives,
                                   candidates_path=candidates, public_path=public,
                                   private_path=private)
    batch = json.loads(public.read_text(encoding="utf-8"))
    form = form_csv(batch)
    form_hashes = {
        "reviewer_a.csv": _write_once(package / "reviewer_a.csv", form),
        "reviewer_b.csv": _write_once(package / "reviewer_b.csv", form),
    }
    adjudication_header = b"sample_id,adjudicator_id,outcome,rationale\n"
    form_hashes["adjudication_template.csv"] = _write_once(
        package / "adjudication_template.csv", adjudication_header)
    audit_bytes = (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode("utf-8")
    audit_hash = _write_once(package / "source_audit.json", audit_bytes)
    rubric_paths = [ROOT / "docs" / "EVALUATOR_RUBRIC.md",
                   ROOT / "docs" / "PHASE4_ANNOTATION_RUBRIC.md",
                   ROOT / "docs" / "PHASE5_HUMAN_REVIEW_PROTOCOL.md"]
    rubric_hashes = {f"rubrics/{path.name}": _write_once(
        package / "rubrics" / path.name, path.read_bytes()) for path in rubric_paths}
    manifest = {
        "package_version": "phase5-independent-review-v2",
        "status": "blank_forms_no_human_judgments",
        "batch_id": audit["batch_id"], "sample_count": audit["blinded_sample_count"],
        "public_batch_sha256": audit["public_sha256"],
        "private_map_sha256": audit["private_map_sha256"],
        "source_audit_sha256": audit_hash,
        "form_sha256": form_hashes,
        "rubric_sha256": rubric_hashes,
        "distribution": "Give each reviewer only their own form and rubric. Retain private join map separately; do not publish raw responses without review.",
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_hash = _write_once(package / "package_manifest.json", manifest_bytes)
    return {"status": manifest["status"], "samples": manifest["sample_count"],
            "package": str(package), "manifest_sha256": manifest_hash}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase4", type=Path, default=DEFAULT_PHASE4)
    parser.add_argument("--output", type=Path, default=DEFAULT_PACKAGE)
    args = parser.parse_args()
    print(json.dumps(prepare(args.phase4, args.output), sort_keys=True))
