"""Provider-neutral, auditable context-integrity canary evidence.

Canaries are evidence about a particular request history.  They do not score
model behaviour and they never turn an unknown provider context claim into a
scientific conclusion by themselves.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping, Sequence


class CanaryStatus(StrEnum):
    VERIFIED = "canary_verified"
    FAILED = "canary_failed"
    NOT_APPLICABLE = "canary_not_applicable"
    UNDETERMINED = "canary_undetermined"


@dataclass(frozen=True, slots=True)
class CanaryPolicy:
    enabled: bool = False
    verification_method: str = "provider_context_evidence"
    marker_prefix: str = "ctx"


@dataclass(frozen=True, slots=True)
class CanaryEvidence:
    marker_id: str
    marker: str
    turn_index: int
    prior_marker_ids: tuple[str, ...]
    status: CanaryStatus
    verification_method: str
    reason: str | None = None
    provider_evidence: Mapping[str, object] = field(default_factory=dict)


def marker_for(*identity: object, prefix: str = "ctx") -> tuple[str, str]:
    digest = hashlib.sha256(":".join(str(item) for item in identity).encode()).hexdigest()
    return f"{prefix}-{digest[:12]}", f"<{prefix}:{digest[:24]}>"


def inject_canary(prompt: str, marker: str) -> str:
    """Make the marker part of the preserved, exported request text.

    The instruction is intentionally low-salience.  It is not a behavioural
    probe and the absence of an echoed marker is *not* interpreted as failure.
    """
    return f"{prompt}\n\n[context-integrity marker {marker}; do not discuss this marker]"


def verify_canary(*, marker_id: str, marker: str, turn_index: int,
                  prior_marker_ids: Sequence[str], metadata: Mapping[str, object],
                  policy: CanaryPolicy) -> CanaryEvidence:
    if not policy.enabled:
        return CanaryEvidence(marker_id, marker, turn_index, tuple(prior_marker_ids),
                              CanaryStatus.NOT_APPLICABLE, policy.verification_method,
                              "canary_policy_disabled")
    signal = metadata.get("canary_verification")
    if signal == "verified":
        return CanaryEvidence(marker_id, marker, turn_index, tuple(prior_marker_ids),
                              CanaryStatus.VERIFIED, policy.verification_method,
                              "provider_reported_context_evidence", dict(metadata))
    if signal == "failed":
        return CanaryEvidence(marker_id, marker, turn_index, tuple(prior_marker_ids),
                              CanaryStatus.FAILED, policy.verification_method,
                              "provider_reported_context_loss", dict(metadata))
    return CanaryEvidence(marker_id, marker, turn_index, tuple(prior_marker_ids),
                          CanaryStatus.UNDETERMINED, policy.verification_method,
                          "provider_context_evidence_unavailable", dict(metadata))
