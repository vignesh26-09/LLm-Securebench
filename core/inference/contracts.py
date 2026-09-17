"""Provider-neutral inference schemas and ports."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping, Protocol

from core.models.registry import ModelMetadata


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Generation controls shared across local, mock, and future API providers."""

    temperature: float = 0.0
    max_new_tokens: int | None = None
    max_tokens: int | None = None
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.temperature < 0:
            raise ValueError("temperature must be non-negative")
        if self.max_new_tokens is not None and self.max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.max_new_tokens is not None and self.max_tokens is not None:
            raise ValueError("Specify max_new_tokens or max_tokens, not both")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def resolved_max_new_tokens(self) -> int:
        """Resolve the compatible max-token aliases to a local-generation limit."""
        return self.max_new_tokens or self.max_tokens or 256


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    model: ModelMetadata
    prompt: str
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    requested_seed: int | None = None


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Structured successful inference outcome with provider-supplied metadata."""

    text: str
    model: ModelMetadata
    provider: str
    latency_ms: float
    token_usage: TokenUsage | None = None
    finish_reason: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


class ContextValidity(StrEnum):
    """Evidence-backed conversation context state."""

    RETAINED = "retained"
    TRUNCATED = "truncated"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: str
    content: str
    turn_index: int
    message_id: str

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant"}:
            raise ValueError("conversation message role is invalid")
        if not self.content or self.turn_index < 0 or not self.message_id:
            raise ValueError("conversation messages require content, non-negative turn index, and identity")


@dataclass(frozen=True, slots=True)
class ConversationRequest:
    model: ModelMetadata
    conversation_id: str
    messages: tuple[ConversationMessage, ...]
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    requested_seed: int | None = None
    system_prompt: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.conversation_id or not self.messages:
            raise ValueError("conversation request requires identity and messages")
        indexes = tuple(message.turn_index for message in self.messages)
        if indexes != tuple(sorted(indexes)):
            raise ValueError("conversation messages must be in turn order")
        if len({message.message_id for message in self.messages}) != len(self.messages):
            raise ValueError("conversation message identities must be unique")


@dataclass(frozen=True, slots=True)
class ConversationResponse:
    text: str
    conversation_id: str
    turn_index: int
    model: ModelMetadata
    provider: str
    latency_ms: float
    context_status: ContextValidity
    token_usage: TokenUsage | None = None
    finish_reason: str | None = None
    requested_seed: int | None = None
    effective_seed: int | None = None
    provider_supports_seed: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)


# Compatibility name for the original skeleton contract.
InferenceResponse = InferenceResult


class InferenceError(RuntimeError):
    """Base error for provider-neutral inference failures."""


class InferenceTimeoutError(InferenceError):
    """Raised when a provider cannot complete within the configured timeout."""


class InferenceProvider(Protocol):
    """Port consumed by benchmark orchestration; no SDK is exposed here."""

    @property
    def provider_name(self) -> str: ...

    def generate(self, request: InferenceRequest) -> InferenceResult: ...


class ConversationInferenceProvider(InferenceProvider, Protocol):
    """Optional provider port for ordered multi-turn requests."""

    def generate_conversation(self, request: ConversationRequest) -> ConversationResponse: ...


class ApiInferenceProvider(InferenceProvider, Protocol):
    """Optional port shape for future remote/API-backed providers."""

    @property
    def endpoint(self) -> str: ...
