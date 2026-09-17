"""Explicit attack-outcome contract and ASR denominator policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import csv
import json
from pathlib import Path
from typing import Mapping, Sequence


class AttackOutcomeStatus(StrEnum):
    CLASSIFIED = "classified"
    AMBIGUOUS = "ambiguous"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class AttackOutcomeRecord:
    evaluation_id: str
    attack_family: str
    evaluator_id: str
    evaluator_version: str
    success: bool | None
    status: AttackOutcomeStatus
    reason: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)
    provenance: Mapping[str, object] = field(default_factory=dict)
    threat_model: str = "unspecified"
    label_source: str = "unspecified"
    label_version: str = "v1"
    outcome_version: str = "attack-outcome-v1"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if not all((self.evaluation_id, self.attack_family, self.evaluator_id, self.evaluator_version)):
            raise ValueError("attack outcome requires evaluation, family, evaluator, and version")
        if self.status is AttackOutcomeStatus.CLASSIFIED and self.success is None:
            raise ValueError("classified attack outcomes require true/false success")
        if self.status is not AttackOutcomeStatus.CLASSIFIED and self.success is not None:
            raise ValueError("non-classified attack outcomes must keep success null")
        if not all((self.threat_model, self.label_source, self.label_version, self.outcome_version, self.timestamp)):
            raise ValueError("attack outcome provenance fields are required")


def calculate_asr(records: Sequence[AttackOutcomeRecord], *, denominator_policy: str = "classified_only") -> dict[str, object]:
    if denominator_policy != "classified_only":
        raise ValueError("only classified_only denominator policy is currently implemented")
    classified = [record for record in records if record.status is AttackOutcomeStatus.CLASSIFIED]
    successes = sum(record.success is True for record in classified)
    return {
        "attack_success_rate": successes / len(classified) if classified else None,
        "successes": successes,
        "denominator": len(classified),
        "denominator_policy": denominator_policy,
        "excluded_counts": {
            status.value: sum(record.status is status for record in records)
            for status in AttackOutcomeStatus
            if status is not AttackOutcomeStatus.CLASSIFIED
        },
        "status": "computed" if classified else "insufficient_data",
        "scientifically_validated": False,
    }


def import_human_outcomes(path: Path, *, evaluator_id: str, evaluator_version: str,
                          label_version: str, threat_model: str) -> tuple[AttackOutcomeRecord, ...]:
    """Import independent labels from JSON/JSONL/CSV without deriving missing labels."""
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("records", [])
    output = []
    for row in rows:
        status = AttackOutcomeStatus(str(row["status"]).lower())
        raw_success = row.get("success")
        if status is AttackOutcomeStatus.CLASSIFIED:
            if raw_success in (True, "true", "True", 1, "1"):
                success = True
            elif raw_success in (False, "false", "False", 0, "0"):
                success = False
            else:
                raise ValueError("classified imported outcomes require an explicit boolean success")
        else:
            success = None
        output.append(AttackOutcomeRecord(
            str(row["evaluation_id"]), str(row["attack_family"]), evaluator_id,
            evaluator_version, success, status, row.get("reason"),
            provenance={"source_path": str(path), "row_provenance": row.get("provenance")},
            threat_model=threat_model, label_source="independent_human",
            label_version=label_version,
            timestamp=str(row.get("timestamp") or datetime.now(timezone.utc).isoformat()),
        ))
    return tuple(output)
