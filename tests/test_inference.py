"""Unit tests for model registry and provider-neutral inference contracts."""

import unittest

from core.inference.contracts import GenerationConfig, InferenceRequest, InferenceTimeoutError
from core.inference.mock import MockInferenceProvider
from core.inference.transformers_provider import LocalTransformersProvider
from core.models.registry import InMemoryModelRegistry, ModelMetadata, ModelNotFoundError


class ModelRegistryTest(unittest.TestCase):
    def test_registry_resolves_metadata(self) -> None:
        model = ModelMetadata("mock-model", "mock", version="1", context_window=1024, capabilities=frozenset({"generate"}))
        registry = InMemoryModelRegistry()
        registry.register(model)
        self.assertEqual(registry.get("mock-model"), model)
        self.assertEqual(registry.list(), (model,))
        with self.assertRaises(ModelNotFoundError):
            registry.get("missing")
        with self.assertRaises(ValueError):
            registry.register(model)


class InferenceContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = ModelMetadata("mock-model", "mock")

    def test_generation_config_validates_and_resolves_aliases(self) -> None:
        self.assertEqual(GenerationConfig(max_tokens=12).resolved_max_new_tokens, 12)
        self.assertEqual(GenerationConfig(max_new_tokens=7).resolved_max_new_tokens, 7)
        with self.assertRaises(ValueError):
            GenerationConfig(max_tokens=1, max_new_tokens=1)
        with self.assertRaises(ValueError):
            GenerationConfig(temperature=-0.1)
        with self.assertRaises(ValueError):
            GenerationConfig(timeout_seconds=0)

    def test_mock_provider_is_deterministic_and_structured(self) -> None:
        provider = MockInferenceProvider({"hello": "world"})
        result = provider.generate(InferenceRequest(self.model, "hello", GenerationConfig(max_new_tokens=4)))
        self.assertEqual(result.text, "world")
        self.assertEqual(result.provider, "mock")
        self.assertEqual(result.model, self.model)
        self.assertEqual(result.finish_reason, "mock")
        self.assertTrue(result.metadata["deterministic"])
        self.assertGreaterEqual(result.latency_ms, 0)

    def test_mock_provider_enforces_timeout(self) -> None:
        provider = MockInferenceProvider(delay_seconds=0.1)
        request = InferenceRequest(self.model, "hello", GenerationConfig(timeout_seconds=0.01))
        with self.assertRaises(InferenceTimeoutError):
            provider.generate(request)

    def test_transformers_provider_does_not_load_at_construction(self) -> None:
        provider = LocalTransformersProvider("not-a-downloaded-model")
        self.assertEqual(provider.provider_name, "local-transformers")
