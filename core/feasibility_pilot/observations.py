"""Redacted, append-only public indexes over restricted raw evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
from datetime import datetime, timezone
from dataclasses import field

from core.feasibility_pilot.cases import digest
from core.feasibility_pilot.restricted_store import (EvidenceConflict, EvidenceSecurityError,
                                                      RestrictedEvidenceStore, _identifier)


@dataclass(frozen=True, slots=True)
class AttemptEvent:
    attempt_id: str
    trial_id: str
    turn_index: int
    attempt_number: int
    event: str
    request_reference: str | None = None
    response_reference: str | None = None
    response_sha256: str | None = None
    finish_reason: str | None = None
    error_code: str | None = None
    provider_input_tokens: int | None = None
    provider_output_tokens: int | None = None
    valid_response: bool | None = None
    recorded_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ObservationLedger:
    def __init__(self, root: Path, restricted: RestrictedEvidenceStore) -> None:
        self.root, self.restricted = Path(root), restricted
        for directory in (self.root / "assignments", self.root / "events",
                          self.root / "observations", self.root / "distance_schedules",
                          self.root / "context_audits"):
            directory.mkdir(parents=True, exist_ok=True)

    def _write(self, relative: Path, value: dict) -> dict:
        normalized = json.loads(json.dumps(value, sort_keys=True))
        payload = {**normalized, "content_sha256": digest(normalized)}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.restricted.assert_public_safe(encoded.decode())
        path = self.root / relative
        try:
            with path.open("xb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            if self._read(relative) != payload:
                raise EvidenceConflict("Append-only public record conflict") from None
        return payload

    def _read(self, relative: Path) -> dict:
        try:
            payload = json.loads((self.root / relative).read_text(encoding="utf-8"))
            hash_value = payload.pop("content_sha256")
            if hash_value != digest(payload):
                raise ValueError
            payload["content_sha256"] = hash_value
            self.restricted.assert_public_safe(json.dumps(payload))
            return payload
        except Exception:
            raise EvidenceSecurityError("Public evidence integrity verification failed") from None

    def assign(self, assignment: object) -> dict:
        from dataclasses import asdict
        trial_id = _identifier(getattr(assignment, "trial_id"))
        lock_path = Path("allocation_lock.json")
        if (self.root / lock_path).exists():
            lock = self._read(lock_path)
            if trial_id not in lock["assignment_hashes"] or digest(asdict(assignment)) != lock["assignment_hashes"][trial_id]:
                raise EvidenceConflict("Assignment is outside frozen denominator")
        return self._write(Path("assignments") / f"{trial_id}.json", asdict(assignment))

    def freeze_assignments(self, assignments: object) -> dict:
        if not getattr(assignments, "frozen", False):
            raise ValueError("Original allocation must be frozen first")
        lock_path = Path("allocation_lock.json")
        if (self.root / lock_path).exists():
            existing = self._read(lock_path)
            if existing["allocation_sha256"] != assignments.sha256:
                raise EvidenceConflict("Frozen allocation cannot be changed")
        records = [self.assign(item) for item in assignments.assignments]
        lock = {"allocation_sha256": assignments.sha256,
                "assignment_hashes": {item["trial_id"]: item["content_sha256"]
                                      for item in records}}
        if len(lock["assignment_hashes"]) != len(records):
            raise EvidenceConflict("Duplicate assignment in frozen denominator")
        if len(tuple((self.root / "assignments").glob("*.json"))) != len(records):
            raise EvidenceConflict("Unplanned assignment exists in public ledger")
        return self._write(lock_path, lock)

    def freeze_distance_schedule(self, schedule: object) -> dict:
        from dataclasses import asdict
        trial_id = _identifier(getattr(schedule, "trial_id"))
        assignment = self._read(Path("assignments") / f"{trial_id}.json")
        if assignment["distance"] != getattr(schedule, "assigned_distance"):
            raise EvidenceConflict("Schedule differs from frozen distance assignment")
        return self._write(Path("distance_schedules") / f"{trial_id}.json",
                           asdict(schedule))

    def distance_schedule(self, trial_id: str) -> dict | None:
        relative = Path("distance_schedules") / f"{_identifier(trial_id)}.json"
        return self._read(relative) if (self.root / relative).exists() else None

    def append_context_audit(self, audit: object) -> dict:
        from dataclasses import asdict
        trial_id = _identifier(getattr(audit, "trial_id"))
        payload = asdict(audit)
        assignment = self._read(Path("assignments") / f"{trial_id}.json")
        schedule = self.distance_schedule(trial_id)
        observation = self.observation(trial_id)
        if (schedule is None
                or payload["assignment_sha256"] != assignment["content_sha256"]
                or payload["distance_schedule_sha256"] != schedule["content_sha256"]
                or payload["observation_sha256"] != (observation["content_sha256"] if observation else None)
                or payload["model_id"] != assignment["model_id"]
                or payload["planned_filler_exchanges"] != schedule["planned_filler_exchanges"]):
            raise EvidenceConflict("Context audit contradicts frozen trial evidence")
        if payload["evidence_class"] != "mock_fixture":
            raise EvidenceConflict("Phase 5 audit accepts mock fixtures only")
        if (payload["scientific_context_status"] == "retained_verified"
                or payload["verified_context_primary_eligible"]
                or payload["contextual_decay_claim_available"]):
            raise EvidenceConflict("Mock evidence cannot become verified-context science")
        return self._write(Path("context_audits") / f"{trial_id}.json", payload)

    def context_audit(self, trial_id: str) -> dict | None:
        relative = Path("context_audits") / f"{_identifier(trial_id)}.json"
        return self._read(relative) if (self.root / relative).exists() else None

    def event(self, event: AttemptEvent) -> dict:
        from dataclasses import asdict
        if event.event not in {"submitted", "response", "pre_submission_failure", "uncertain_failure"}:
            raise ValueError("Unknown attempt event")
        if event.finish_reason is not None and event.finish_reason not in {
            "stop", "length", "mock", "eos", "unknown"}:
            raise ValueError("Untrusted finish reason cannot enter public log")
        attempt_id = _identifier(event.attempt_id)
        return self._write(Path("events") / f"{attempt_id}.{event.event}.json", asdict(event))

    def read_event(self, attempt_id: str, event: str) -> dict | None:
        relative = Path("events") / f"{_identifier(attempt_id)}.{_identifier(event)}.json"
        return self._read(relative) if (self.root / relative).exists() else None

    def complete(self, trial_id: str, value: dict) -> dict:
        trial_id = _identifier(trial_id)
        value = {key: item for key, item in value.items() if key != "content_sha256"}
        if value.get("trial_id") != trial_id:
            raise ValueError("Observation identity mismatch")
        allowed = {"trial_id", "assignment_sha256", "plan_sha256", "arm", "distance",
                   "matching_set_id", "evidence_class", "execution_provenance",
                   "live_primary_eligible_arm",
                   "status", "reason", "attempt_event_hashes", "realized_refusals",
                   "distance_schedule_sha256", "planned_filler_exchanges",
                   "realized_complete_filler_exchanges",
                   "provider_input_tokens", "provider_output_tokens",
                   "planned_matching_status", "planned_matching_reasons",
                   "realized_matching_status", "outcome_status", "checker_version",
                   "y_final", "y_earlier", "y_ever",
                   "earlier_exact_observed_in_partial_trajectory",
                   "final_response_sha256", "earlier_response_sha256", "recorded_at_utc"}
        if set(value) != allowed:
            raise ValueError("Public observation schema forbids raw or missing fields")
        assignment = self._read(Path("assignments") / f"{trial_id}.json")
        expected_class = "scripted_mechanism" if assignment["arm"] == "S" else "live_feasibility_pilot"
        if (value["assignment_sha256"] != assignment["content_sha256"]
                or value["arm"] != assignment["arm"]
                or value["distance"] != assignment["distance"]
                or value["matching_set_id"] != assignment["matching_set_id"]
                or value["evidence_class"] != expected_class
                or value["execution_provenance"] != "mock_fixture"
                or value["live_primary_eligible_arm"] != (assignment["arm"] in {"A", "T"})):
            raise EvidenceConflict("Observation contradicts frozen allocation or evidence class")
        schedule = self.distance_schedule(trial_id)
        if (schedule is None or value["distance_schedule_sha256"] != schedule["content_sha256"]
                or value["planned_filler_exchanges"] != schedule["planned_filler_exchanges"]
                or not 0 <= value["realized_complete_filler_exchanges"] <= value["planned_filler_exchanges"]):
            raise EvidenceConflict("Observation contradicts frozen distance schedule")
        if value["status"] != "completed" and any(value[key] is not None for key in (
                "y_final", "y_earlier", "y_ever")):
            raise ValueError("Incomplete observation must preserve null outcomes")
        return self._write(Path("observations") / f"{trial_id}.json", value)

    def observation(self, trial_id: str) -> dict | None:
        relative = Path("observations") / f"{_identifier(trial_id)}.json"
        return self._read(relative) if (self.root / relative).exists() else None

    def coverage(self) -> dict:
        lock = self._read(Path("allocation_lock.json"))
        assignments = lock["assignment_hashes"]
        for trial_id, expected in assignments.items():
            actual = self._read(Path("assignments") / f"{_identifier(trial_id)}.json")
            if actual["content_sha256"] != expected:
                raise EvidenceSecurityError("Frozen assignment integrity failed")
        if len(tuple((self.root / "assignments").glob("*.json"))) != len(assignments):
            raise EvidenceSecurityError("Unplanned assignment in frozen ledger")
        observations = tuple((self.root / "observations").glob("*.json"))
        rows = [self._read(Path("observations") / item.name) for item in observations]
        if any(row["trial_id"] not in assignments for row in rows):
            raise EvidenceSecurityError("Observation is outside frozen denominator")
        if any(row["assignment_sha256"] != assignments[row["trial_id"]] for row in rows):
            raise EvidenceSecurityError("Observation assignment hash mismatch")
        return {"assigned": len(assignments), "observed": len(rows),
                "completed": sum(row["status"] == "completed" for row in rows),
                "failed": sum(row["status"] != "completed" for row in rows),
                "missing": len(assignments) - len(rows),
                "null_outcomes": sum(row["y_final"] is None for row in rows)}

    def live_primary_rows(self) -> tuple[dict, ...]:
        """Assigned A/T arm projection, not the verified-context estimator."""
        self.coverage()  # Verify the frozen denominator and observation hashes.
        rows = [self._read(Path("observations") / path.name)
                for path in (self.root / "observations").glob("*.json")]
        return tuple(row for row in rows if row["evidence_class"] == "live_feasibility_pilot"
                     and row["arm"] in {"A", "T"} and row["live_primary_eligible_arm"])

    def verified_context_primary_rows(self) -> tuple[dict, ...]:
        """Only completed A/T rows with an affirmative independent context audit."""
        eligible = []
        for row in self.live_primary_rows():
            audit = self.context_audit(row["trial_id"])
            if (row["status"] == "completed" and row["y_final"] in {0, 1}
                    and audit is not None
                    and audit["observation_sha256"] == row["content_sha256"]
                    and audit["scientific_context_status"] == "retained_verified"
                    and audit["verified_context_primary_eligible"] is True
                    and audit["evidence_class"] != "mock_fixture"
                    and row.get("execution_provenance") != "mock_fixture"):
                eligible.append(row)
        return tuple(eligible)
