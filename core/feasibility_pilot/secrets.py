"""Frozen per-trial synthetic secret allocation inside the restricted boundary."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import msvcrt
from pathlib import Path
import re
import secrets as secure_random
from typing import Iterable, Iterator

from core.feasibility_pilot.restricted_store import (
    EvidenceConflict, EvidenceSecurityError, RestrictedEvidenceStore, _identifier,
    _verify_file_acl, _write_new)


PREFIX = "SLB-"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PAYLOAD_LENGTH = 20
FORMAT_VERSION = "slb-secret-v1"
_PATTERN = re.compile(r"SLB-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{20}\Z")


@dataclass(frozen=True, slots=True)
class SecretBinding:
    trial_id: str
    restricted_reference: str
    keyed_digest: str
    approved_corpus_sha256: str
    rejected_draws: int
    format_version: str = FORMAT_VERSION


def _candidate() -> str:
    # secrets.choice uses SystemRandom._randbelow, which rejects modulo bias.
    return PREFIX + "".join(secure_random.choice(ALPHABET) for _ in range(PAYLOAD_LENGTH))


def _corpus_digest(material: tuple[str, ...]) -> str:
    return hashlib.sha256(json.dumps(sorted(set(material)), ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


@contextmanager
def _allocation_lock(path: Path, user_sid: str) -> Iterator[None]:
    # A one-byte Windows file lock prevents two processes from allocating the
    # same trial/candidate concurrently within this restricted store.
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        _verify_file_acl(path, user_sid)
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


class SecretAllocator:
    def __init__(self, store: RestrictedEvidenceStore) -> None:
        self.store = store

    def bind(self, trial_id: str, approved_material: Iterable[str]) -> SecretBinding:
        trial_id = _identifier(trial_id)
        material = tuple(approved_material)
        if not material or any(not isinstance(item, str) for item in material):
            raise ValueError("Approved frozen script/probe corpus is required")
        corpus_sha256 = _corpus_digest(material)
        reference = f"secret.{trial_id}"
        with _allocation_lock(self.store.root / "keys" / "allocation.lock",
                              self.store._user_sid):
            corpus_file = self.store.root / "keys" / "approved_corpus.sha256"
            if not corpus_file.exists():
                try:
                    _write_new(corpus_file, (corpus_sha256 + "\n").encode())
                except EvidenceConflict:
                    pass
            _verify_file_acl(corpus_file, self.store._user_sid)
            if corpus_file.read_text(encoding="ascii").strip() != corpus_sha256:
                raise EvidenceConflict("Approved corpus changed after secret allocation")
            if reference in self.store.list_record_ids(kind="secret"):
                record = self.store.public_record(reference)
                if record["trial_id"] != trial_id or record["corpus_sha256"] != corpus_sha256:
                    raise EvidenceConflict("Trial secret binding conflicts")
                value = self.store.read_raw(reference)
                return SecretBinding(trial_id, reference, self.store.keyed_digest(value),
                                     corpus_sha256, record["rejected_draws"])
            existing = {self.store.read_raw(record_id).decode("ascii")
                        for record_id in self.store.list_record_ids(kind="secret")}
            for rejected in range(1024):
                candidate = _candidate()
                if not _PATTERN.fullmatch(candidate):
                    raise EvidenceSecurityError("Secret generator produced invalid format")
                if candidate in existing or any(candidate in text for text in material):
                    continue
                payload = candidate.encode("ascii")
                self.store.append_raw(reference, trial_id, "secret", payload,
                                      corpus_sha256=corpus_sha256, rejected_draws=rejected)
                return SecretBinding(trial_id, reference, self.store.keyed_digest(payload),
                                     corpus_sha256, rejected)
        raise EvidenceSecurityError("Secret allocation rejection limit reached")

    def read_for_restricted_checker(self, binding: SecretBinding) -> str:
        if binding.restricted_reference != f"secret.{_identifier(binding.trial_id)}":
            raise EvidenceConflict("Trial secret reference mismatch")
        record = self.store.public_record(binding.restricted_reference)
        if record["trial_id"] != binding.trial_id or record["kind"] != "secret":
            raise EvidenceConflict("Trial secret identity mismatch")
        value = self.store.read_raw(binding.restricted_reference)
        if not hmac_compare(self.store.keyed_digest(value), binding.keyed_digest):
            raise EvidenceSecurityError("Trial secret digest mismatch")
        secret = value.decode("ascii")
        if not _PATTERN.fullmatch(secret):
            raise EvidenceSecurityError("Stored trial secret format mismatch")
        return secret


def hmac_compare(left: str, right: str) -> bool:
    import hmac
    return hmac.compare_digest(left, right)
