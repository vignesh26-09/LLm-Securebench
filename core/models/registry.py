"""Provider-neutral model metadata and registry contracts."""

from dataclasses import dataclass, field
from typing import Mapping, Protocol


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Stable model identity and optional capability/provenance metadata."""

    name: str
    provider: str
    version: str | None = None
    context_window: int | None = None
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, object] = field(default_factory=dict)


# Retained as a compatibility name for existing callers.
ModelDescriptor = ModelMetadata


class ModelRegistry(Protocol):
    """Resolves provider-neutral model metadata by registered name."""

    def get(self, name: str) -> ModelMetadata: ...

    def list(self) -> tuple[ModelMetadata, ...]: ...


class ModelNotFoundError(KeyError):
    """Raised when a requested model has not been registered."""


class InMemoryModelRegistry:
    """Small explicit registry suitable for composition roots and tests."""

    def __init__(self, models: tuple[ModelMetadata, ...] = ()) -> None:
        self._models = {model.name: model for model in models}

    def register(self, model: ModelMetadata) -> None:
        if model.name in self._models:
            raise ValueError(f"Model already registered: {model.name}")
        self._models[model.name] = model

    def get(self, name: str) -> ModelMetadata:
        try:
            return self._models[name]
        except KeyError as error:
            raise ModelNotFoundError(name) from error

    def list(self) -> tuple[ModelMetadata, ...]:
        return tuple(self._models.values())
