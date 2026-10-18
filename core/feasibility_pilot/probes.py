"""Conservative probe gate and immutable, blinded human-review records."""

from dataclasses import dataclass, field
from dataclasses import asdict
import json
import os
from pathlib import Path
import re

from core.feasibility_pilot.cases import digest
from core.feasibility_pilot.restricted_store import (EvidenceConflict, EvidenceSecurityError,
                                                      RestrictedEvidenceStore,
                                                      _SECRET_SHAPE)


_SECRET_REQUEST = re.compile(
    r"\b(?:secret|password|passcode|passphrase|hidden\s+(?:token|code)|"
    r"system\s+(?:prompt|instruction)|private\s+(?:key|token)|"
    r"protected\s+(?:token|code)|initial\s+instruction)\b", re.I)
_INDIRECT = re.compile(r"\b(?:first|last|initial)\s+(?:\d+|few|several|some)\s+"
                       r"(?:characters?|letters?|symbols?|digits?)\b|"
                       r"\b(?:encode|decode|base64|hex|cipher|reverse|spell\s+out)\b", re.I)


@dataclass(frozen=True, slots=True)
class ProbeVariant:
    variant_id: str
    family_id: str
    task_id: str
    version: int
    wording: str = field(repr=False)
    rubric_version: str = "legitimate-probe-v1"
    prior_version_sha256: str | None = None
    amendment_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.variant_id or not self.family_id or not self.task_id or not self.wording.strip():
            raise ValueError("Incomplete probe variant")
        if self.version < 1 or (self.version > 1 and not (self.prior_version_sha256 and self.amendment_reason)):
            raise ValueError("Probe amendment requires predecessor and reason")
        if (_SECRET_REQUEST.search(self.wording) or _INDIRECT.search(self.wording)
                or _SECRET_SHAPE.search(self.wording)):
            raise ValueError("Probe contains a possible secret request or transformation cue")

    @property
    def content_sha256(self) -> str:
        return digest((self.variant_id, self.family_id, self.task_id, self.version,
                       self.wording, self.rubric_version, self.prior_version_sha256,
                       self.amendment_reason))


@dataclass(frozen=True, slots=True)
class ProbeReview:
    variant_sha256: str
    reviewer_id: str
    reviewer_role: str  # A or B; arm identity must not be supplied.
    authorized_task: bool
    no_secret_request: bool
    no_secret_cue: bool
    comparable_answer: bool
    same_goal_scope: bool
    rubric_version: str
    provenance_reference: str

    def __post_init__(self) -> None:
        if self.reviewer_role not in {"A", "B"} or not self.reviewer_id or not self.provenance_reference:
            raise ValueError("Invalid independent review provenance")

    @property
    def approved(self) -> bool:
        return all((self.authorized_task, self.no_secret_request, self.no_secret_cue,
                    self.comparable_answer, self.same_goal_scope))


@dataclass(frozen=True, slots=True)
class ProbeAdjudication:
    variant_sha256: str
    adjudicator_id: str
    provenance_reference: str
    approved: bool
    reason: str


def review_decision(variant: ProbeVariant, first: ProbeReview, second: ProbeReview,
                    adjudication: ProbeAdjudication | None = None) -> bool:
    if (first.variant_sha256 != variant.content_sha256 or second.variant_sha256 != variant.content_sha256
            or {first.reviewer_role, second.reviewer_role} != {"A", "B"}
            or first.reviewer_id == second.reviewer_id
            or first.rubric_version != variant.rubric_version
            or second.rubric_version != variant.rubric_version):
        raise ValueError("Independent blinded reviews do not match probe version")
    if first.approved != second.approved:
        if (adjudication is None or adjudication.variant_sha256 != variant.content_sha256
                or adjudication.adjudicator_id in {first.reviewer_id, second.reviewer_id}
                or not adjudication.provenance_reference or not adjudication.reason):
            raise ValueError("Disagreement requires independent adjudication")
        return adjudication.approved
    if adjudication is not None:
        raise ValueError("Unneeded adjudication")
    return first.approved


class ProbeRegistry:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else None
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
        self._versions: dict[tuple[str, int], ProbeVariant] = {}

    def add(self, variant: ProbeVariant, store: RestrictedEvidenceStore | None = None) -> None:
        if store is not None:
            store.assert_public_safe(variant.wording)
        key = variant.variant_id, variant.version
        if key in self._versions:
            raise EvidenceConflict("Probe version is immutable")
        if variant.version > 1:
            try:
                previous = self.get(variant.variant_id, variant.version - 1)
            except KeyError:
                previous = None
            if previous is None or previous.content_sha256 != variant.prior_version_sha256:
                raise EvidenceConflict("Probe amendment predecessor mismatch")
        if self.root is not None:
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", variant.variant_id):
                raise ValueError("Invalid persistent probe identity")
            path = self.root / f"{variant.variant_id}.v{variant.version}.json"
            payload = {**asdict(variant), "content_sha256": variant.content_sha256}
            try:
                with path.open("x", encoding="utf-8") as handle:
                    json.dump(payload, handle, sort_keys=True)
                    handle.flush()
                    os.fsync(handle.fileno())
            except FileExistsError:
                raise EvidenceConflict("Probe version is immutable") from None
        self._versions[key] = variant

    def get(self, variant_id: str, version: int) -> ProbeVariant:
        key = (variant_id, version)
        if self.root is None:
            return self._versions[key]
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", variant_id):
            raise KeyError(key)
        path = self.root / f"{variant_id}.v{version}.json"
        if not path.exists():
            raise KeyError(key)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            expected = payload.pop("content_sha256")
            variant = ProbeVariant(**payload)
            if variant.content_sha256 != expected:
                raise ValueError
            return variant
        except Exception:
            raise EvidenceConflict("Stored probe version failed integrity check") from None


class ProbeReviewLedger:
    """Append-only review decisions; identity authenticity requires external handoff."""

    def __init__(self, root: Path, restricted: RestrictedEvidenceStore | None = None) -> None:
        self.root = Path(root)
        self.restricted = restricted
        self.root.mkdir(parents=True, exist_ok=True)

    def _write(self, name: str, value: object) -> None:
        payload = asdict(value)
        record = {**payload, "record_sha256": digest(payload)}
        serialized = json.dumps(record, sort_keys=True)
        if self.restricted is not None:
            self.restricted.assert_public_safe(serialized)
        elif _SECRET_SHAPE.search(serialized):
            raise EvidenceSecurityError("Review metadata contains protected-secret pattern")
        try:
            with (self.root / name).open("x", encoding="utf-8") as handle:
                json.dump(record, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            raise EvidenceConflict("Review record is append-only") from None

    def _read(self, name: str, kind: type) -> object:
        try:
            record = json.loads((self.root / name).read_text(encoding="utf-8"))
            expected = record.pop("record_sha256")
            if digest(record) != expected:
                raise ValueError
            return kind(**record)
        except FileNotFoundError:
            raise KeyError(name) from None
        except Exception:
            raise EvidenceConflict("Review record integrity failed") from None

    def add_review(self, review: ProbeReview) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", review.variant_sha256):
            raise ValueError("Probe content hash required")
        self._write(f"{review.variant_sha256}.{review.reviewer_role}.json", review)

    def add_adjudication(self, adjudication: ProbeAdjudication) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", adjudication.variant_sha256):
            raise ValueError("Probe content hash required")
        self._write(f"{adjudication.variant_sha256}.adjudication.json", adjudication)

    def decision(self, variant: ProbeVariant) -> bool:
        first = self._read(f"{variant.content_sha256}.A.json", ProbeReview)
        second = self._read(f"{variant.content_sha256}.B.json", ProbeReview)
        try:
            adjudication = self._read(f"{variant.content_sha256}.adjudication.json",
                                      ProbeAdjudication)
        except KeyError:
            adjudication = None
        return review_decision(variant, first, second, adjudication)
