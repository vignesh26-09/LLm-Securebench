"""Compatibility exports for provider-neutral inference contracts."""

from core.inference.contracts import (
    ConversationInferenceProvider,
    ConversationMessage,
    ConversationRequest,
    ConversationResponse,
    InferenceProvider,
    InferenceRequest,
    InferenceResponse,
    InferenceResult,
)

InferenceClient = InferenceProvider

__all__ = ["InferenceClient", "InferenceProvider", "InferenceRequest", "InferenceResponse", "InferenceResult",
           "ConversationInferenceProvider", "ConversationMessage", "ConversationRequest", "ConversationResponse"]
