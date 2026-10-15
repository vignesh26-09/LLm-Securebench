"""Windows-only restricted, immutable feasibility evidence boundary.

Raw payloads are never returned by the public projection. Construction fails
closed unless the NTFS ACL can be reduced and verified before key creation.
"""

from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


DEFAULT_ROOT = Path(r"F:\SecureLLM\experiments\feasibility_pilot\restricted")
_ID = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
_SECRET_SHAPE = re.compile(r"SLB-[A-Z2-9]{20}")
_KINDS = frozenset({"secret", "prompt", "response", "history", "rendering"})
_SCHEMA_VERSION = 1


class EvidenceSecurityError(RuntimeError):
    """Sanitized failure; never includes protected material."""


class EvidenceConflict(EvidenceSecurityError):
    """An immutable record ID already names different evidence."""


def _local_free(pointer: object) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    kernel32.LocalFree(pointer)


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or _SECRET_SHAPE.search(value):
        raise ValueError("Invalid opaque evidence identifier")
    return value


def _current_user_sid() -> str:
    try:
        result = subprocess.run(["whoami", "/user", "/fo", "csv", "/nh"],
                                check=True, capture_output=True, text=True, timeout=10)
        import csv
        sid = next(csv.reader([result.stdout.strip()]))[1]
        if not re.fullmatch(r"S-1-[0-9-]+", sid):
            raise ValueError
        return sid
    except (OSError, subprocess.SubprocessError, IndexError, ValueError) as exc:
        raise EvidenceSecurityError("Execution-account identity unavailable") from exc


def _acl_details(path: Path) -> dict:
    # Read the actual DACL via Windows APIs. A nested PowerShell process can
    # fail module autoload under some Python environments without a nonzero
    # exit code, which would make a shell-based check unsafe.
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    descriptor = ctypes.c_void_p()
    dacl = ctypes.c_void_p()
    get_info = security.GetNamedSecurityInfoW
    get_info.argtypes = [ctypes.c_wchar_p, wintypes.DWORD, wintypes.DWORD,
                         ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
                         ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    get_info.restype = wintypes.DWORD
    status = get_info(str(path), 1, 0x4, None, None, ctypes.byref(dacl),
                      None, ctypes.byref(descriptor))
    if status != 0:
        raise EvidenceSecurityError("Restricted ACL could not be read")
    try:
        convert = security.ConvertSecurityDescriptorToStringSecurityDescriptorW
        convert.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                            ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(wintypes.DWORD)]
        convert.restype = wintypes.BOOL
        text = ctypes.c_wchar_p()
        length = wintypes.DWORD()
        if not convert(descriptor, 1, 0x4, ctypes.byref(text), ctypes.byref(length)):
            raise EvidenceSecurityError("Restricted ACL could not be decoded")
        try:
            sddl = text.value or ""
        finally:
            _local_free(ctypes.cast(text, ctypes.c_void_p))
        return {"Protected": sddl.startswith("D:P"), "Rules": [
            {"Type": "Allow" if fields[0] == "A" else "Other",
             "Inherited": "ID" in fields[1], "Rights": fields[2], "Sid": fields[5]}
            for ace in re.findall(r"\(([^()]*)\)", sddl)
            if len(fields := ace.split(";")) == 6]}
    finally:
        _local_free(descriptor)


def _secure_directory(path: Path, user_sid: str) -> None:
    if os.name != "nt":
        raise EvidenceSecurityError("Restricted evidence requires Windows NTFS and DPAPI")
    if path.is_symlink():
        raise EvidenceSecurityError("Restricted evidence path cannot be a symlink")
    path.mkdir(parents=True, exist_ok=True)
    allowed = {user_sid, "S-1-5-18", "S-1-5-32-544"}
    canonical = {user_sid, "SY", "BA"}  # SDDL aliases for SYSTEM/Administrators.
    grants = [f"*{sid}:(OI)(CI)F" for sid in sorted(allowed)]
    try:
        subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", *grants],
                       check=True, capture_output=True, text=True, timeout=15)
        acl = _acl_details(path)
        rules = acl.get("Rules") or []
        if isinstance(rules, dict):
            rules = [rules]
        if (acl.get("Protected") is not True or not rules
                or any(rule.get("Inherited") or rule.get("Type") != "Allow"
                       or rule.get("Sid") not in canonical for rule in rules)
                or not any(rule.get("Sid") == user_sid and rule.get("Rights") == "FA"
                           for rule in rules)):
            raise EvidenceSecurityError("Restricted ACL verification failed")
    except (OSError, subprocess.SubprocessError) as exc:
        raise EvidenceSecurityError("Restricted ACL could not be installed") from exc


class _Blob(ctypes.Structure):
    _fields_ = [("length", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(data: bytes, *, protect: bool) -> bytes:
    if os.name != "nt":
        raise EvidenceSecurityError("DPAPI is unavailable")
    source = ctypes.create_string_buffer(data)
    input_blob = _Blob(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
    output_blob = _Blob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    operation = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    operation.restype = wintypes.BOOL
    if protect:
        operation.argtypes = [ctypes.POINTER(_Blob), ctypes.c_wchar_p, ctypes.c_void_p,
                              ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD,
                              ctypes.POINTER(_Blob)]
    else:
        operation.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p,
                              ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD,
                              ctypes.POINTER(_Blob)]
    if not operation(ctypes.byref(input_blob), None, None, None, None, 0x1,
                     ctypes.byref(output_blob)):
        raise EvidenceSecurityError("Protected key operation failed")
    try:
        return ctypes.string_at(output_blob.data, output_blob.length)
    finally:
        _local_free(output_blob.data)


def _write_new(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise EvidenceConflict("Immutable evidence ID already exists") from exc


def _verify_file_acl(path: Path, user_sid: str) -> None:
    if path.is_symlink():
        raise EvidenceSecurityError("Restricted evidence file cannot be a symlink")
    rules = _acl_details(path).get("Rules") or []
    if (not rules or any(rule.get("Type") != "Allow"
                         or rule.get("Sid") not in {user_sid, "SY", "BA"}
                         for rule in rules)
            or not any(rule.get("Sid") == user_sid for rule in rules)):
        raise EvidenceSecurityError("Restricted evidence file ACL verification failed")


class RestrictedEvidenceStore:
    """Explicitly opened restricted store; never initializes at import time."""

    def __init__(self, root: Path = DEFAULT_ROOT) -> None:
        self.root = Path(root)
        if any(component.is_symlink() for component in (self.root, *self.root.parents)):
            raise EvidenceSecurityError("Restricted evidence path cannot traverse a symlink")
        self._user_sid = _current_user_sid()
        for directory in (self.root, self.root / "keys", self.root / "raw"):
            _secure_directory(directory, self._user_sid)
        key_path = self.root / "keys" / "master.v1.dpapi"
        if not key_path.exists():
            pending_key = self.root / "keys" / f".pending-key-{secrets.token_hex(16)}"
            try:
                _write_new(pending_key, _dpapi(secrets.token_bytes(32), protect=True))
                _verify_file_acl(pending_key, self._user_sid)
                try:
                    os.rename(pending_key, key_path)  # No overwrite on Windows.
                except FileExistsError:
                    pass  # Another initializer won; verify its key below.
            finally:
                pending_key.unlink(missing_ok=True)
        _verify_file_acl(key_path, self._user_sid)
        try:
            self._key = _dpapi(key_path.read_bytes(), protect=False)
            if len(self._key) != 32:
                raise EvidenceSecurityError("Protected key has invalid length")
            self._mac_key = hmac.new(self._key, b"feasibility-hmac-key-v1",
                                     hashlib.sha256).digest()
        except OSError as exc:
            raise EvidenceSecurityError("Protected key could not be read") from exc

    def _path(self, record_id: str) -> Path:
        return self.root / "raw" / f"{_identifier(record_id)}.json"

    def keyed_digest(self, payload: bytes) -> str:
        return hmac.new(self._mac_key, b"secret-digest-v1\0" + payload,
                        hashlib.sha256).hexdigest()

    def _content_digest(self, payload: bytes) -> str:
        return hmac.new(self._mac_key, b"record-content-v1\0" + payload,
                        hashlib.sha256).hexdigest()

    def append_raw(self, record_id: str, trial_id: str, kind: str, payload: bytes,
                   *, version: int = 1, previous_id: str | None = None,
                   corpus_sha256: str | None = None, rejected_draws: int = 0) -> dict:
        record_id, trial_id = _identifier(record_id), _identifier(trial_id)
        if kind not in _KINDS or not isinstance(payload, bytes) or not payload:
            raise ValueError("Invalid restricted evidence type")
        if type(version) is not int or version < 1 or (version == 1) != (previous_id is None):
            raise ValueError("Invalid evidence version chain")
        if previous_id is not None:
            previous = self.public_record(previous_id)
            if previous["trial_id"] != trial_id or previous["version"] != version - 1:
                raise EvidenceConflict("Evidence predecessor mismatch")
        if corpus_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", corpus_sha256):
            raise ValueError("Invalid approved-corpus digest")
        if type(rejected_draws) is not int or rejected_draws < 0:
            raise ValueError("Invalid rejection count")
        header = {"schema_version": _SCHEMA_VERSION, "record_id": record_id,
                  "trial_id": trial_id, "kind": kind, "version": version,
                  "previous_id": previous_id, "corpus_sha256": corpus_sha256,
                  "rejected_draws": rejected_draws}
        destination = self._path(record_id)
        if destination.exists():
            stored, prior = self._read_record(record_id)
            if stored != header or prior != payload:
                raise EvidenceConflict("Immutable evidence ID conflicts")
            return self.public_record(record_id)
        aad = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self._key).encrypt(nonce, payload, aad)
        envelope = {**header, "nonce": base64.b64encode(nonce).decode(),
                    "ciphertext": base64.b64encode(ciphertext).decode(),
                    "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
                    "plaintext_hmac": self._content_digest(payload)}
        temporary = self.root / "raw" / f".pending-{secrets.token_hex(16)}"
        try:
            _write_new(temporary, json.dumps(envelope, sort_keys=True).encode())
            _verify_file_acl(temporary, self._user_sid)
            try:
                os.rename(temporary, destination)  # Windows: atomic and no overwrite.
            except FileExistsError:
                stored, prior = self._read_record(record_id)
                if stored != header or prior != payload:
                    raise EvidenceConflict("Immutable evidence ID conflicts")
            return self.public_record(record_id)
        finally:
            temporary.unlink(missing_ok=True)

    def _read_record(self, record_id: str) -> tuple[dict, bytes]:
        try:
            path = self._path(record_id)
            _verify_file_acl(path, self._user_sid)
            envelope = json.loads(path.read_text(encoding="utf-8"))
            header = {key: envelope[key] for key in (
                "schema_version", "record_id", "trial_id", "kind", "version",
                "previous_id", "corpus_sha256", "rejected_draws")}
            if header["schema_version"] != _SCHEMA_VERSION or header["record_id"] != record_id:
                raise ValueError
            nonce = base64.b64decode(envelope["nonce"], validate=True)
            ciphertext = base64.b64decode(envelope["ciphertext"], validate=True)
            if len(nonce) != 12 or hashlib.sha256(ciphertext).hexdigest() != envelope["ciphertext_sha256"]:
                raise ValueError
            aad = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
            payload = AESGCM(self._key).decrypt(nonce, ciphertext, aad)
            if not hmac.compare_digest(self._content_digest(payload), envelope["plaintext_hmac"]):
                raise ValueError
            return header, payload
        except Exception:
            # Integrity failures must never quote a tampered raw payload in an
            # ordinary exception.
            raise EvidenceSecurityError("Restricted evidence integrity verification failed") from None

    def read_raw(self, record_id: str) -> bytes:
        return self._read_record(record_id)[1]

    def public_record(self, record_id: str) -> dict:
        header, _ = self._read_record(record_id)
        return {**header, "evidence_class": "restricted_feasibility_evidence",
                "record_sha256": hashlib.sha256(self._path(record_id).read_bytes()).hexdigest()}

    def list_record_ids(self, *, kind: str | None = None) -> tuple[str, ...]:
        result = []
        for path in sorted((self.root / "raw").glob("*.json")):
            record_id = path.stem
            header, _ = self._read_record(record_id)
            if kind is None or header["kind"] == kind:
                result.append(record_id)
        return tuple(result)

    def assert_public_safe(self, content: str) -> None:
        if _SECRET_SHAPE.search(content):
            raise EvidenceSecurityError("Public content contains protected-secret pattern")
        for record_id in self.list_record_ids(kind="secret"):
            secret = self.read_raw(record_id).decode("ascii")
            if secret in content:
                raise EvidenceSecurityError("Public content contains protected material")

    def export_public(self) -> dict:
        projection = {"schema_version": _SCHEMA_VERSION,
                      "records": [self.public_record(record_id) for record_id in self.list_record_ids()]}
        self.assert_public_safe(json.dumps(projection, sort_keys=True))
        return projection
