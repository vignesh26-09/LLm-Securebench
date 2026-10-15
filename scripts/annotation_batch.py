"""Export blinded research samples and import independently supplied human labels.

Input candidates are researcher-prepared pointers to persisted evaluation evidence.
This tool never calls a model or generates a label.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session
from core.evaluation.annotation_workflow import (create_annotation_batch,
    persist_annotation_import, validate_annotation_import)
from core.persistence.database import Base, make_engine


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--candidates", type=Path, required=True)
    export.add_argument("--public", type=Path, required=True)
    export.add_argument("--private-map", type=Path, required=True)
    export.add_argument("--batch-id", required=True)
    export.add_argument("--rubric-version", required=True)
    imported = commands.add_parser("import")
    imported.add_argument("--public", type=Path, required=True)
    imported.add_argument("--private-map", type=Path, required=True)
    imported.add_argument("--judgments", type=Path, required=True)
    imported.add_argument("--adjudications", type=Path, required=True)
    imported.add_argument("--label-version", required=True)
    imported.add_argument("--database", type=Path, default=ROOT / "securellmbench.db")
    args = parser.parse_args()
    if args.command == "export":
        if args.public.resolve() == args.private_map.resolve():
            raise SystemExit("Rater-facing export and private map must have different paths")
        value = _read(args.candidates)
        candidates = value["candidates"] if isinstance(value, dict) else value
        if isinstance(value, dict) and value.get("synthetic_fixture") is True:
            candidates = [{**row, "synthetic_fixture": True} for row in candidates]
        public, private = create_annotation_batch(candidates, batch_id=args.batch_id,
            rubric_version=args.rubric_version, salt=secrets.token_hex(24),
            shuffle_seed=secrets.randbits(64))
        _write_new(args.private_map, private)
        _write_new(args.public, public)
        print(json.dumps({"batch_id": args.batch_id, "samples": len(public["items"]),
                          "public": str(args.public), "private_map": str(args.private_map)}))
        return
    public, private = _read(args.public), _read(args.private_map)
    judgments, adjudications = _read(args.judgments), _read(args.adjudications)
    if not isinstance(judgments, list) or not isinstance(adjudications, list):
        raise SystemExit("Judgments and adjudications must each be JSON arrays")
    validated = validate_annotation_import(public, private, judgments, adjudications,
                                           label_version=args.label_version)
    engine = make_engine(f"sqlite:///{args.database.resolve()}")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            persist_annotation_import(session, validated, private)
    finally:
        engine.dispose()
    print(json.dumps({"batch_id": validated["batch_id"], "samples": validated["sample_count"],
                      "disagreements": validated["disagreements"], "status": "human_labels_imported"}))


if __name__ == "__main__":
    main()
