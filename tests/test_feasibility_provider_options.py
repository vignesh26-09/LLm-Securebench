"""Mock transport tests for opt-in top-p and honest settings evidence."""

import io
import json
import unittest
from unittest.mock import patch

from core.inference.contracts import (ConversationMessage, ConversationRequest,
                                      GenerationConfig, InferenceError, InferenceRequest)
from core.inference.ollama_provider import OllamaProvider
from core.inference.openai_compatible_provider import OpenAICompatibleProvider
from core.inference.transformers_provider import LocalTransformersProvider
from core.models.registry import ModelMetadata


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class ProviderOptionsTests(unittest.TestCase):
    def setUp(self):
        self.model = ModelMetadata("qwen3.5:2b", "ollama-local", "a" * 64,
                                   context_window=8192)
        self.provider = OllamaProvider(seed=42)

    def _fake_http(self, expected_path, result):
        sent = []

        def post(request, **_):
            self.assertTrue(request.full_url.endswith(expected_path))
            sent.append(json.loads(request.data))
            return _Response(json.dumps(result).encode())

        return sent, post

    def test_conversation_transports_explicit_controls_without_claiming_effective_values(self):
        sent, post = self._fake_http("/api/chat", {"done": True,
            "message": {"content": "done"}, "prompt_eval_count": 10, "eval_count": 1})
        request = ConversationRequest(self.model, "conv", (
            ConversationMessage("user", "hello", 0, "m0"),),
            GenerationConfig(temperature=0.7, top_p=0.8, max_new_tokens=17),
            requested_seed=19, system_prompt="harmless instruction")
        with patch("core.inference.ollama_provider.urlopen", side_effect=post):
            response = self.provider.generate_conversation(request)
        self.assertEqual(sent[0]["options"], {"temperature": 0.7,
            "num_predict": 17, "seed": 19, "top_p": 0.8, "num_ctx": 8192})
        self.assertEqual(sent[0]["messages"][0]["role"], "system")
        self.assertEqual(response.metadata["requested_options"], sent[0]["options"])
        self.assertIsNone(response.metadata["effective_options"])

    def test_old_default_omits_top_p(self):
        sent, post = self._fake_http("/api/generate", {"done": True, "response": "ok"})
        with patch("core.inference.ollama_provider.urlopen", side_effect=post):
            result = self.provider.generate(InferenceRequest(self.model, "hello"))
        self.assertNotIn("top_p", sent[0]["options"])
        self.assertIsNone(result.metadata["effective_options"])

    def test_unsupported_top_p_values_are_rejected_before_http(self):
        for value in (-0.1, 0, 1.1, float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                GenerationConfig(top_p=value)

    def test_transformers_adapter_rejects_unimplemented_top_p_before_loading_weights(self):
        provider = LocalTransformersProvider("unused-local-path")
        with self.assertRaisesRegex(InferenceError, "top_p is unsupported"):
            provider.generate(InferenceRequest(self.model, "harmless",
                                               GenerationConfig(top_p=0.8)))

    def test_openai_compatible_adapter_does_not_silently_drop_top_p(self):
        provider = OpenAICompatibleProvider("https://example.test/v1")
        sent, post = self._fake_http("/chat/completions", {
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]})
        with patch("core.inference.openai_compatible_provider.urlopen", side_effect=post):
            provider.generate(InferenceRequest(self.model, "harmless",
                                               GenerationConfig(top_p=0.8)))
        self.assertEqual(sent[0]["top_p"], 0.8)
