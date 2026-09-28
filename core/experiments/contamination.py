"""Session-isolation evidence for isolated-control comparisons."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import json
from pathlib import Path
from typing import Mapping

from core.experiments.models import utc_now


class IsolationStatus(StrEnum):
    VERIFIED = "isolation_verified"
    UNVERIFIABLE = "isolation_unverifiable"
    SUSPECTED_LEAK = "isolation_suspected_leak"
    CANNOT_DETERMINE = "isolation_cannot_be_determined"


@dataclass(frozen=True, slots=True)
class SessionContaminationRecord:
    record_id: str
    sequential_observation_id: str
    isolated_observation_id: str
    sequential_conversation_id: str
    isolated_conversation_id: str
    provider: str
    status: IsolationStatus
    created_at: str
    reason: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)


class ContaminationLedgerStore:
    """Append-only local ledger; database persistence uses the generic artifact adapter."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, value: SessionContaminationRecord) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{value.record_id}.json"
        if path.exists():
            return
        path.write_text(json.dumps({**value.__dict__} if hasattr(value, "__dict__") else {
            "record_id": value.record_id, "sequential_observation_id": value.sequential_observation_id,
            "isolated_observation_id": value.isolated_observation_id,
            "sequential_conversation_id": value.sequential_conversation_id,
            "isolated_conversation_id": value.isolated_conversation_id, "provider": value.provider,
            "status": value.status.value, "created_at": value.created_at, "reason": value.reason,
            "evidence": dict(value.evidence)}, indent=2, sort_keys=True), encoding="utf-8")

    def all(self) -> tuple[SessionContaminationRecord, ...]:
        if not self.root.exists():
            return ()
        output = []
        for path in sorted(self.root.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            output.append(SessionContaminationRecord(**{**raw, "status": IsolationStatus(raw["status"])}))
        return tuple(output)


def assess_isolation(*, record_id: str, sequential_observation_id: str,
                     isolated_observation_id: str, sequential_conversation_id: str,
                     isolated_conversation_id: str, provider: str,
                     sequential_metadata: Mapping[str, object],
                     isolated_metadata: Mapping[str, object]) -> SessionContaminationRecord:
    if sequential_conversation_id == isolated_conversation_id:
        status, reason = IsolationStatus.SUSPECTED_LEAK, "shared_conversation_identifier"
    elif isolated_metadata.get("cache_bypass") is True and isolated_metadata.get("provider_state_scope") == "request":
        status, reason = IsolationStatus.VERIFIED, "provider_reported_request_scoped_cache_bypass"
    elif not sequential_conversation_id or not isolated_conversation_id:
        status, reason = IsolationStatus.CANNOT_DETERMINE, "missing_conversation_identifier"
    else:
        status, reason = IsolationStatus.UNVERIFIABLE, "provider_cache_isolation_evidence_unavailable"
    return SessionContaminationRecord(record_id, sequential_observation_id, isolated_observation_id,
                                      sequential_conversation_id, isolated_conversation_id, provider,
                                      status, utc_now(), reason,
                                      {"sequential_provider_metadata": dict(sequential_metadata),
                                       "isolated_provider_metadata": dict(isolated_metadata)})
