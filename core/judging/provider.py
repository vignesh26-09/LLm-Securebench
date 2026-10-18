"""Provider port for structured Layer 2 judge output."""

from dataclasses import dataclass, field
from typing import Mapping, Protocol

from core.judging.models import JudgeConfig


@dataclass(frozen=True, slots=True)
class JudgeProviderRequest:
    prompt: str
    config: JudgeConfig


@dataclass(frozen=True, slots=True)
class JudgeProviderResponse:
    raw_output: str
    generation_metadata: Mapping[str, object] = field(default_factory=dict)


class JudgeProviderError(RuntimeError):
    """Base failure for a provider-neutral judge adapter."""


class JudgeTimeoutError(JudgeProviderError):
    """Raised when a judge provider exceeds its configured timeout."""


class JudgeProvider(Protocol):
    """Port used by Layer 2; no judge SDK or model family leaks into callers."""
    @property
    def provider_name(self) -> str: ...

    def judge(self, request: JudgeProviderRequest) -> JudgeProviderResponse: ...
