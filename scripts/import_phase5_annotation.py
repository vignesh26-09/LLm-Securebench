"""Validate two filled reviewer forms and import real labels only after human review.

Default mode validates and reports agreement without writing; --commit appends to
the specified database. This script never invents or predicts judgments.
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

from sqlalchemy.orm import Session

from core.evaluation.annotation_workflow import persist_annotation_import, validate_annotation_import
from core.evaluation.phase5_annotation import (adjudications_from_form, audit_annotation_batch,
                                               independent_agreement, judgments_from_forms)
from core.persistence.database import Base, make_engine


def verify_package(package: Path, *, public_path: Path, private_path: Path,
                   batch_id: str, sample_count: int) -> dict[str, object]:
    """Bind an import to the immutable, versioned reviewer instructions."""
    manifest_path = package / "package_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("package_version") != "phase5-independent-review-v2"
            or manifest.get("status") != "blank_forms_no_human_judgments"
            or manifest.get("batch_id") != batch_id
            or manifest.get("sample_count") != sample_count):
        raise ValueError("annotation package identity or sample count differs")
    checks = {public_path: manifest.get("public_batch_sha256"),
              private_path: manifest.get("private_map_sha256"),
              package / "source_audit.json": manifest.get("source_audit_sha256")}
    for group in ("form_sha256", "rubric_sha256"):
        entries = manifest.get(group)
        if not isinstance(entries, dict) or not entries:
            raise ValueError(f"annotation package {group} is missing")
        checks.update({package / name: digest for name, digest in entries.items()})
    for path, expected in checks.items():
        if (not isinstance(expected, str) or len(expected) != 64
                or not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise ValueError(f"annotation package file or hash differs: {path.name}")
    return {"package_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "rubric_sha256": manifest["rubric_sha256"]}


def run(*, phase4: Path, reviewer_a: Path, reviewer_b: Path, adjudications: Path,
        label_version: str, database: Path, commit: bool = False,
        package: Path = ROOT / "experiments" / "phase5" / "restricted_annotation_v2") -> dict[str, object]:
    restricted = phase4 / "restricted_annotation"
    public_path = restricted / "blinded_batch_v1.json"
    private_path = restricted / "private_join_map_v1.json"
    audit = audit_annotation_batch(
        observations_dir=phase4 / "jbb_pilot_run_v1" / "observations",
        objectives_path=phase4 / "jbb_annotation_objectives_v1.json",
        candidates_path=restricted / "candidates_v1.json",
        public_path=public_path, private_path=private_path)
    public = json.loads(public_path.read_text(encoding="utf-8"))
    private = json.loads(private_path.read_text(encoding="utf-8"))
    package_provenance = verify_package(package, public_path=public_path,
        private_path=private_path, batch_id=str(audit["batch_id"]),
        sample_count=int(audit["blinded_sample_count"]))
    judgments = judgments_from_forms(public, reviewer_a, reviewer_b)
    decisions = adjudications_from_form(adjudications)
    agreement = independent_agreement(judgments)
    validated = validate_annotation_import(public, private, judgments, decisions,
                                           label_version=label_version)
    if commit:
        engine = make_engine(f"sqlite:///{database.resolve()}")
        try:
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                persist_annotation_import(session, validated, private,
                                          extra_provenance=package_provenance)
        finally:
            engine.dispose()
    return {"status": "human_labels_imported" if commit else "validated_not_imported",
            "batch_id": audit["batch_id"], "sample_count": validated["sample_count"],
            "independent_judgments": len(judgments),
            "adjudications": len(decisions), "agreement_before_adjudication": agreement,
            "label_version": label_version,
            "package_manifest_sha256": package_provenance["package_manifest_sha256"],
            "database": str(database) if commit else None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase4", type=Path, default=ROOT / "experiments" / "phase4")
    parser.add_argument("--package", type=Path, default=ROOT / "experiments" / "phase5" / "restricted_annotation_v2")
    parser.add_argument("--reviewer-a", type=Path, required=True)
    parser.add_argument("--reviewer-b", type=Path, required=True)
    parser.add_argument("--adjudications", type=Path, required=True)
    parser.add_argument("--label-version", required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    try:
        result = run(phase4=args.phase4, reviewer_a=args.reviewer_a,
                     reviewer_b=args.reviewer_b, adjudications=args.adjudications,
                     label_version=args.label_version, database=args.database,
                     commit=args.commit, package=args.package)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, f"annotation validation failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))
