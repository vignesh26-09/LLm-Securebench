import io
import json
import unittest
from unittest.mock import patch

from core.inference.contracts import GenerationConfig, InferenceRequest
from core.inference.openai_compatible_provider import OpenAICompatibleProvider, normalize_endpoint
from core.models.registry import ModelMetadata


class OpenAICompatibleProviderTests(unittest.TestCase):
    def test_normalizes_base_url_and_rejects_insecure_remote_url(self):
        self.assertEqual(normalize_endpoint('https://example.test/api'), 'https://example.test/api/v1/chat/completions')
        self.assertEqual(normalize_endpoint('http://127.0.0.1:9000/v1'), 'http://127.0.0.1:9000/v1/chat/completions')
        with self.assertRaises(ValueError):
            normalize_endpoint('http://example.test/v1')
        with self.assertRaises(ValueError):
            normalize_endpoint('https://user:secret@example.test/v1')

    def test_sends_openai_compatible_request_without_persisting_key(self):
        value = {'model': 'remote-model', 'choices': [{'message': {'content': 'answer'}, 'finish_reason': 'stop'}],
                 'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5}}
        provider = OpenAICompatibleProvider('https://example.test/v1', api_key='ephemeral-key')
        request = InferenceRequest(ModelMetadata('remote-model', 'openai-compatible'), 'prompt', GenerationConfig(max_new_tokens=12))
        with patch('core.inference.openai_compatible_provider.urlopen', return_value=io.BytesIO(json.dumps(value).encode())) as call:
            result = provider.generate(request)
        sent = call.call_args.args[0]
        self.assertEqual(sent.full_url, 'https://example.test/v1/chat/completions')
        self.assertEqual(sent.get_header('Authorization'), 'Bearer ephemeral-key')
        self.assertEqual(json.loads(sent.data)['max_tokens'], 12)
        self.assertEqual(result.text, 'answer')
        self.assertEqual(result.token_usage.total_tokens, 5)
        self.assertNotIn('ephemeral-key', repr(result.metadata))
