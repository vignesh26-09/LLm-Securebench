import io
import json
import unittest
from unittest.mock import patch

from core.judging.models import JudgeConfig
from core.judging.ollama_provider import OllamaJudgeProvider
from core.judging.provider import JudgeProviderRequest, JudgeTimeoutError


class OllamaJudgeProviderTests(unittest.TestCase):
    def config(self) -> JudgeConfig:
        return JudgeConfig(
            provider_name="ollama-local-judge",
            model="judge-model",
            model_version="digest",
            methodology_version="layer2-local-judge-v1",
            prompt_version="prompt-v1",
            rubric_version="rubric-v1",
            temperature=0.0,
            seed=7,
            timeout_seconds=1,
        )

    def test_preserves_raw_output_and_generation_metadata(self):
        tags = {"models": [{"name": "judge-model", "digest": "digest"}]}
        generated = {"done": True, "response": "{\"dimension\":\"instruction_following\",\"score\":1,\"label\":\"pass\",\"confidence\":0.6,\"explanation\":\"ok\",\"evidence_citations\":[],\"metadata\":{}}", "done_reason": "stop"}

        def fake_urlopen(request, timeout=0):
            return io.BytesIO(json.dumps(generated).encode())

        with patch("core.judging.ollama_provider.installed_models", return_value=tags["models"]), patch("core.judging.ollama_provider.urlopen", side_effect=fake_urlopen) as call:
            response = OllamaJudgeProvider().judge(JudgeProviderRequest("prompt", self.config()))
        self.assertEqual(response.raw_output, generated["response"])
        self.assertEqual(response.generation_metadata["provider"], "ollama-local-judge")
        self.assertFalse(response.generation_metadata["measurement_semantics"].startswith("ground truth"))
        sent = json.loads(call.call_args.args[0].data)
        self.assertEqual(sent["format"], "json")
        self.assertEqual(sent["options"]["seed"], 7)

    def test_uninstalled_model_rejected_before_generation(self):
        with patch("core.judging.ollama_provider.installed_models", return_value=[]):
            with self.assertRaisesRegex(Exception, "not installed"):
                OllamaJudgeProvider().judge(JudgeProviderRequest("prompt", self.config()))

    def test_timeout_is_typed(self):
        with patch.object(OllamaJudgeProvider, "assert_model_installed", return_value="digest"), patch("core.judging.ollama_provider.urlopen", side_effect=TimeoutError):
            with self.assertRaises(JudgeTimeoutError):
                OllamaJudgeProvider().judge(JudgeProviderRequest("prompt", self.config()))


if __name__ == "__main__":
    unittest.main()
