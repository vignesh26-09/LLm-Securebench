"""Build a traceable 10,000-prompt engineering corpus; never generate labels."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.dataset.normalization import normalize_text


SOURCES = {
    "dolly": {
        "repository": "databricks/databricks-dolly-15k",
        "revision": "bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a",
        "file": "databricks-dolly-15k.jsonl",
        "sha256": "2df9083338b4abd6bceb5635764dab5d833b393b55759dffb0959b6fcbf794ec",
        "license": "CC-BY-SA-3.0",
    },
    "anthropic": {
        "repository": "Anthropic/hh-rlhf",
        "revision": "09be8c5bbc57cb3887f3a9732ad6aa7ec602a1fa",
        "file": "red-team-attempts/red_team_attempts.jsonl.gz",
        "sha256": "4c7b0069991460f0064f279fd400b51f3f0095697d14d7793c49b0925f80814f",
        "license": "MIT (repository metadata)",
    },
}
SELECTION_VERSION = "mixed-source-10000-v1"
_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d ().-]{7,}\d)(?!\d)")


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _download(name: str, destination: Path) -> None:
    spec = SOURCES[name]
    url = ("https://huggingface.co/datasets/" + spec["repository"] +
           "/resolve/" + spec["revision"] + "/" + spec["file"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if _sha256(destination) != spec["sha256"]:
            raise ValueError(f"Existing {name} source checksum mismatch")
        return
    pending = destination.with_suffix(destination.suffix + ".pending")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, pending.open("xb") as output:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                output.write(block)
            output.flush()
            os.fsync(output.fileno())
        if _sha256(pending) != spec["sha256"]:
            raise ValueError(f"Downloaded {name} source checksum mismatch")
        pending.rename(destination)
    finally:
        pending.unlink(missing_ok=True)


def _eligible(text: str | None) -> str | None:
    prompt = normalize_text(text)
    if (not prompt or not 10 <= len(prompt) <= 4000 or _EMAIL.search(prompt)
            or _PHONE.search(prompt)):
        return None
    return prompt


def _rank(record: dict) -> str:
    return hashlib.sha256((SELECTION_VERSION + ":" + record["id"]).encode()).hexdigest()


def _candidates(dolly_path: Path, anthropic_path: Path) -> tuple[list[dict], list[dict], dict]:
    if _sha256(dolly_path) != SOURCES["dolly"]["sha256"]:
        raise ValueError("Dolly source checksum mismatch")
    if _sha256(anthropic_path) != SOURCES["anthropic"]["sha256"]:
        raise ValueError("Anthropic source checksum mismatch")
    benign: dict[str, dict] = {}
    dolly_rows = 0
    with dolly_path.open(encoding="utf-8") as source:
        for index, line in enumerate(source):
            dolly_rows += 1
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("context"), str):
                raise ValueError("Dolly source row schema mismatch")
            if row["context"].strip():
                continue  # An instruction without its supplied context is incomplete.
            prompt = _eligible(row.get("instruction"))
            if prompt is None:
                continue
            key = prompt.casefold()
            benign.setdefault(key, {
                "id": f"dolly-{index:05d}", "prompt": prompt,
                "category": "benign_control_source", "source": "databricks/databricks-dolly-15k",
                "metadata": {"source_row": index, "source_revision": SOURCES["dolly"]["revision"],
                             "source_sha256": SOURCES["dolly"]["sha256"],
                             "source_category": row.get("category"),
                             "extraction": "instruction_with_empty_context",
                             "outcome_label_status": "not_collected"},
            })
    with gzip.open(anthropic_path, "rt", encoding="utf-8") as source:
        anthropic_rows = json.load(source)
    if not isinstance(anthropic_rows, list):
        raise ValueError("Anthropic source must be a JSON array")
    red_team: dict[str, dict] = {}
    for index, row in enumerate(anthropic_rows):
        if not isinstance(row, dict) or not isinstance(row.get("transcript"), str):
            raise ValueError("Anthropic source row schema mismatch")
        transcript = row["transcript"].lstrip()
        if not transcript.startswith("Human:") or "\n\nAssistant:" not in transcript:
            continue
        # Preserve only the first user turn. A historical multistep transcript
        # must never masquerade as a live defender-generated history.
        first_turn = transcript[len("Human:"):].partition("\n\nAssistant:")[0]
        prompt = _eligible(first_turn)
        if prompt is None:
            continue
        key = prompt.casefold()
        red_team.setdefault(key, {
            "id": f"anthropic-redteam-{index:05d}", "prompt": prompt,
            "category": "red_team_source_seed", "source": "Anthropic/hh-rlhf/red-team-attempts",
            "metadata": {"source_row": index, "source_revision": SOURCES["anthropic"]["revision"],
                         "source_sha256": SOURCES["anthropic"]["sha256"],
                         "extraction": "first_human_turn_only_no_assistant_history",
                         "outcome_label_status": "not_collected",
                         "standalone_attack_validity": "not_reviewed"},
        })
    return (sorted(benign.values(), key=_rank), sorted(red_team.values(), key=_rank),
            {"dolly_source_rows": dolly_rows, "anthropic_source_rows": len(anthropic_rows),
             "unique_eligible_benign": len(benign), "unique_eligible_red_team_seeds": len(red_team)})


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"Existing versioned output differs: {path.name}")
        return
    with path.open("xb") as target:
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())


def build_corpus(dolly_path: Path, anthropic_path: Path, output_path: Path,
                 manifest_path: Path, *, per_group: int = 5000) -> dict:
    """Materialize two explicitly distinct source groups without invented labels."""
    if per_group < 1:
        raise ValueError("per_group must be positive")
    benign, red_team, inventory = _candidates(dolly_path, anthropic_path)
    red_selected = red_team[:per_group]
    red_keys = {row["prompt"].casefold() for row in red_selected}
    benign_selected = [row for row in benign if row["prompt"].casefold() not in red_keys][:per_group]
    if len(red_selected) != per_group or len(benign_selected) != per_group:
        raise ValueError("Insufficient distinct source prompts for requested balanced count")
    # Interleaving gives every complete even-sized batch equal source coverage.
    records = [row for pair in zip(red_selected, benign_selected) for row in pair]
    if len({row["prompt"].casefold() for row in records}) != 2 * per_group:
        raise AssertionError("Source deduplication failed")
    encoded = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
                       for row in records)
    corpus_sha256 = hashlib.sha256(encoded).hexdigest()
    manifest = {
        "schema_version": SELECTION_VERSION,
        "name": "mixed-source-engineering-10000" if per_group == 5000 else "mixed-source-test",
        "record_count": len(records),
        "category_counts": {"benign_control_source": per_group,
                            "red_team_source_seed": per_group},
        "inventory": inventory,
        "source_provenance": SOURCES,
        "selection": "SHA-256 rank by version and source row ID; first user turn only for red-team transcripts; empty-context Dolly instructions; normalized exact-prompt deduplication; 10-4000 characters; obvious email/phone pattern exclusion; groups interleaved",
        "dataset_sha256": corpus_sha256,
        "scientifically_validated": False,
        "outcome_labels_available": False,
        "limitations": ["Red-team first turns may require omitted conversational context and are not validated standalone attacks.",
                        "Dolly instructions are benign task sources, not matched controls for an attack objective.",
                        "Obvious identifier filtering does not certify absence of personal information.",
                        "No attack-success, refusal or model-safety labels are created by this import."],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_immutable(output_path, encoded)
    _write_immutable(manifest_path, manifest_bytes)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch only the two pinned source files")
    parser.add_argument("--dolly", type=Path, default=ROOT / "data/external/dolly_15k_bdd27f4.jsonl")
    parser.add_argument("--anthropic", type=Path, default=ROOT / "data/external/anthropic_red_team_09be8c5.jsonl.gz")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/benchmark_10000.jsonl")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/benchmark_10000.manifest.json")
    args = parser.parse_args()
    if args.download:
        _download("dolly", args.dolly)
        _download("anthropic", args.anthropic)
    manifest = build_corpus(args.dolly, args.anthropic, args.output, args.manifest)
    print(json.dumps({"record_count": manifest["record_count"],
                      "category_counts": manifest["category_counts"],
                      "dataset_sha256": manifest["dataset_sha256"],
                      "scientifically_validated": False}, sort_keys=True))


if __name__ == "__main__":
    main()
