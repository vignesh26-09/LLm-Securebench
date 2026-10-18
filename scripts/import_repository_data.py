"""Import the existing example input losslessly; never generate result artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
from sqlalchemy.orm import Session
from core.dataset.loaders import JsonDatasetLoader
from core.dataset.benchmark_catalog import BenchmarkSelection, LARGE_KEY, load_selection
from core.persistence.database import Base, make_engine
from core.persistence.models import DatasetEntity, DatasetVersionEntity

ROOT = Path(__file__).resolve().parents[1]


def import_example(session, source=ROOT / "data/raw/example.json"):
    raw = source.read_bytes()
    domain = JsonDatasetLoader().load(source)
    payload = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    dataset_id = "repository:example"
    version_id = f"{dataset_id}:{digest}"
    with session.begin():
        dataset = session.get(DatasetEntity, dataset_id)
        if dataset is None:
            session.add(DatasetEntity(id=dataset_id, name=domain.metadata.name,
                description="Repository example input; engineering-only, not a validated research corpus.",
                provenance={"source": "data/raw/example.json", "kind": "repository_example",
                            "scientifically_validated": False, "importer": "scripts.import_repository_data"}))
            session.flush()
        existing = session.get(DatasetVersionEntity, version_id)
        if existing is not None:
            if existing.payload != payload or existing.content_hash != digest:
                raise ValueError("Existing snapshot differs; append-only import refused")
            return {"imported": False, "sha256": digest, "source_records": len(domain.records)}
        session.add(DatasetVersionEntity(id=version_id, dataset_id=dataset_id,
            version=domain.metadata.version.version, content_hash=digest, payload=payload))
    return {"imported": True, "sha256": digest, "source_records": len(domain.records)}


def import_large_source_manifest(session, selection: BenchmarkSelection):
    """Record a source-native large-corpus manifest without exposing all prompts in the API."""
    if selection.key != LARGE_KEY or selection.manifest is None:
        raise ValueError("Expected verified large-corpus selection")
    payload = {"manifest": selection.manifest, "source_path": "data/processed/benchmark_10000.jsonl",
               "record_count": selection.source_count,
               "note": "Prompt text remains in the local, Git-ignored source file."}
    with session.begin():
        dataset = session.get(DatasetEntity, selection.dataset_id)
        if dataset is None:
            session.add(DatasetEntity(id=selection.dataset_id, name=selection.manifest["name"],
                description="Versioned mixed-source engineering corpus; no validated attack outcomes.",
                provenance={"kind": selection.evidence_class, "source_sha256": selection.source_sha256,
                            "scientifically_validated": False,
                            "importer": "scripts.import_repository_data.import_large_source_manifest"}))
            session.flush()
        existing = session.get(DatasetVersionEntity, selection.version_id)
        if existing is not None:
            if existing.payload != payload or existing.content_hash != selection.source_sha256:
                raise ValueError("Existing large-corpus version differs; append-only import refused")
            return {"imported": False, "sha256": selection.source_sha256,
                    "source_records": selection.source_count}
        session.add(DatasetVersionEntity(id=selection.version_id, dataset_id=selection.dataset_id,
            version=selection.manifest["schema_version"], content_hash=selection.source_sha256,
            payload=payload))
    return {"imported": True, "sha256": selection.source_sha256,
            "source_records": selection.source_count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--large", action="store_true", help="Import the verified 10,000-case source manifest")
    args = parser.parse_args()
    engine = make_engine(f"sqlite:///{ROOT / 'securellmbench.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        result = (import_large_source_manifest(session, load_selection(LARGE_KEY))
                  if args.large else import_example(session))
        print(json.dumps(result))


if __name__ == "__main__":
    main()
