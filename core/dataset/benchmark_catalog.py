"""Allowlisted, checksum-verified dataset selections for local engineering runs."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from core.dataset.loaders import JsonDatasetLoader, JsonlDatasetLoader
from core.dataset.models import Dataset


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT / "data/raw/example.json"
LARGE_PATH = ROOT / "data/processed/benchmark_10000.jsonl"
LARGE_MANIFEST = ROOT / "data/benchmark_10000.manifest.json"
LARGE_KEY = "mixed-source-10000-v1"
EXAMPLE_KEY = "repository-example"
MAX_JOB_CASES = 10000


@dataclass(frozen=True)
class BenchmarkSelection:
    key: str
    dataset: Dataset
    source_path: Path
    source_sha256: str
    dataset_id: str
    version_id: str
    source_count: int
    offset: int
    count: int
    evidence_class: str
    manifest: dict | None = None


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def dataset_options() -> list[dict]:
    example = JsonDatasetLoader().load(EXAMPLE_PATH)
    options = [{"id": EXAMPLE_KEY, "name": "Repository example", "case_count": len(example.records),
                "available": True, "category_counts": {"example": len(example.records)},
                "evidence_class": "engineering_example", "max_cases_per_job": len(example.records),
                "note": "Three example inputs; engineering smoke only."}]
    available = LARGE_PATH.is_file() and LARGE_MANIFEST.is_file()
    manifest = None
    if available:
        try:
            manifest = json.loads(LARGE_MANIFEST.read_text(encoding="utf-8"))
            available = (manifest.get("schema_version") == LARGE_KEY
                         and manifest.get("record_count") == 10000
                         and manifest.get("scientifically_validated") is False
                         and _sha256(LARGE_PATH) == manifest.get("dataset_sha256"))
        except (OSError, ValueError):
            available = False
    options.append({"id": LARGE_KEY, "name": "10,000 sourced prompts",
                    "case_count": 10000, "available": bool(available),
                    "category_counts": manifest.get("category_counts", {}) if available else {},
                    "evidence_class": "unvalidated_mixed_source",
                    "max_cases_per_job": MAX_JOB_CASES,
                    "note": ("5,000 benign task sources + 5,000 first-turn red-team seeds; "
                             "full user-facing runs cover all 10,000; no attack-success labels or validated safety rating.")
                            if available else "Build and verify the pinned local source corpus first."})
    return options


def load_selection(key: str = EXAMPLE_KEY, *, offset: int = 0,
                   count: int | None = None) -> BenchmarkSelection:
    if key not in {EXAMPLE_KEY, LARGE_KEY}:
        raise ValueError("Unknown benchmark dataset")
    if type(offset) is not int or offset < 0:
        raise ValueError("Case offset must be nonnegative")
    if key == EXAMPLE_KEY:
        source = EXAMPLE_PATH
        all_data = JsonDatasetLoader().load(source)
        evidence_class = "engineering_example"
        dataset_id = "repository:example"
        manifest = None
        max_cases = len(all_data.records)
    else:
        option = next(item for item in dataset_options() if item["id"] == LARGE_KEY)
        if not option["available"]:
            raise ValueError("Pinned 10,000-case corpus is unavailable or checksum-invalid")
        source = LARGE_PATH
        all_data = JsonlDatasetLoader().load(source)
        manifest = json.loads(LARGE_MANIFEST.read_text(encoding="utf-8"))
        if len(all_data.records) != manifest["record_count"]:
            raise ValueError("Corpus record count conflicts with source manifest")
        if len({row.prompt.casefold() for row in all_data.records if row.prompt}) != len(all_data.records):
            raise ValueError("Corpus contains duplicate prompts")
        evidence_class = "unvalidated_mixed_source"
        dataset_id = "external:mixed-source-10000-v1"
        max_cases = MAX_JOB_CASES
    source_count = len(all_data.records)
    if count is None:
        count = source_count
    if type(count) is not int or count < 1 or count > max_cases:
        raise ValueError(f"Case count must be between 1 and {max_cases}")
    if offset + count > source_count:
        raise ValueError("Selected case window exceeds source corpus")
    selected = Dataset(records=all_data.records[offset:offset + count], metadata=all_data.metadata)
    digest = _sha256(source)
    return BenchmarkSelection(key, selected, source, digest, dataset_id,
                              f"{dataset_id}:{digest}", source_count, offset, count,
                              evidence_class, manifest)
