import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from apps.api.main import create_app
from core.inference.contracts import InferenceRequest, InferenceError, InferenceTimeoutError
from core.inference.mock import MockInferenceProvider
from core.inference.ollama_provider import OllamaProvider
from core.models.registry import ModelMetadata
from scripts.run_local_benchmark import run_model

INVENTORY = [{'name': 'test-model', 'digest': 'test-digest', 'capabilities': ['thinking']}]


class LocalExecutionTests(unittest.TestCase):
    def test_provider_preserves_tokens_finish_reason_and_options(self):
        value = {'done': True, 'response': 'actual text', 'done_reason': 'length', 'prompt_eval_count': 3, 'eval_count': 4}
        with patch('core.inference.ollama_provider.urlopen', return_value=io.BytesIO(json.dumps(value).encode())) as call:
            result = OllamaProvider(seed=7).generate(InferenceRequest(ModelMetadata('test-model', 'ollama-local', capabilities=frozenset({'thinking'})), 'prompt'))
        self.assertEqual(result.token_usage.total_tokens, 7)
        self.assertEqual(result.finish_reason, 'length')
        sent = json.loads(call.call_args.args[0].data)
        self.assertFalse(sent['think'])
        self.assertFalse(sent['stream'])
        self.assertEqual(sent['options']['seed'], 7)

    def test_incomplete_response_and_timeout_are_not_successes(self):
        with patch('core.inference.ollama_provider.urlopen', return_value=io.BytesIO(b'{"done": false, "response": "partial"}')):
            with self.assertRaises(InferenceError):
                OllamaProvider().generate(InferenceRequest(ModelMetadata('test', 'local'), 'prompt'))
        with patch('core.inference.ollama_provider.urlopen', side_effect=TimeoutError):
            with self.assertRaises(InferenceTimeoutError):
                OllamaProvider().generate(InferenceRequest(ModelMetadata('test', 'local'), 'prompt'))

    def test_real_pipeline_persistence_with_explicit_test_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            url = f'sqlite:///{Path(directory) / "test.db"}'
            app = create_app(url)
            outcome = run_model('test-model', database_url=url, provider=MockInferenceProvider(), inventory=INVENTORY, output_directory=Path(directory) / 'artifacts')
            client = TestClient(app)
            self.assertEqual(outcome['completed'], 3)
            counts = client.get('/dashboard-summary').json()['counts']
            self.assertEqual(counts['evaluations'], 3)
            self.assertEqual(counts['layer1-results'], 9)
            self.assertEqual(counts['scientific-records'], 7)
            self.assertEqual(counts['model-scores'], 1)
            model_scores = client.get('/model-scores').json()
            self.assertEqual(model_scores['total'], 1)
            self.assertEqual(model_scores['items'][0]['model_name'], 'test-model')
            self.assertEqual(model_scores['items'][0]['status'], 'engineering_only')
            self.assertIn('model_score', model_scores['items'][0]['formula'])
            report = client.get(f"/benchmark-runs/{outcome['run_id']}/report")
            self.assertEqual(report.status_code, 200)
            payload = report.json()
            self.assertEqual(payload['execution']['completed_cases'], 3)
            self.assertEqual(payload['execution']['total_cases'], 3)
            self.assertEqual(payload['model_score']['status'], 'engineering_only')
            self.assertEqual(payload['selection']['status'], 'evidence_review_required')
            self.assertIn('not confirmed successful attacks', payload['interpretation']['observed_detector_signals'])
            self.assertEqual(len(payload['cases']), 3)
            for record in client.get('/scientific-records').json()['items']:
                self.assertFalse(record['provenance']['scientifically_validated'])
                self.assertTrue(record['provenance']['synthetic_fixture'])
                if record['family'] == 'draa': self.assertIsNone(record['payload']['risk_score'])
                if record['family'] == 'pri': self.assertIsNone(record['payload']['scalar_pri'])
                if record['family'] == 'ml':
                    self.assertEqual(record['status'], 'blocked')
                    self.assertEqual(record['payload']['reason'], 'no_independent_outcome_labels')
            app.state.session_factory.kw['bind'].dispose()

    def test_uninstalled_model_is_rejected_before_execution(self):
        with self.assertRaises(ValueError):
            run_model('missing', inventory=INVENTORY)

    def test_execution_requires_explicit_enablement_and_local_origin(self):
        client = TestClient(create_app('sqlite:///:memory:'), client=('127.0.0.1', 50000))
        self.assertEqual(client.post('/internal/benchmark-jobs', json={'model': 'test-model'}).status_code, 403)
        client = TestClient(create_app('sqlite:///:memory:', enable_local_runs=True), client=('127.0.0.1', 50000))
        for headers in ({}, {'X-SecureLLM-Local': '1', 'Origin': 'https://external.example'}):
            self.assertEqual(client.post('/internal/benchmark-jobs', json={'model': 'test-model'}, headers=headers).status_code, 403)
        with patch('apps.api.local_execution.installed_models', return_value=INVENTORY):
            self.assertEqual(client.post('/internal/benchmark-jobs', json={'model': 'missing'}, headers={'X-SecureLLM-Local': '1'}).status_code, 422)
            with patch('apps.api.local_execution.threading.Thread'):
                first = client.post('/internal/benchmark-jobs', json={'model': 'test-model'}, headers={'X-SecureLLM-Local': '1'})
                self.assertEqual(first.status_code, 202)
                self.assertEqual(client.get(f"/benchmark-jobs/{first.json()['id']}").status_code, 200)
                self.assertEqual(client.post('/internal/benchmark-jobs', json={'model': 'test-model'}, headers={'X-SecureLLM-Local': '1'}).status_code, 409)

    def test_discovery_failure_is_separate_from_empty_inventory(self):
        client = TestClient(create_app('sqlite:///:memory:'))
        with patch('apps.api.local_execution.installed_models', side_effect=InferenceError('offline')):
            self.assertFalse(client.get('/runtime-models').json()['available'])
        with patch('apps.api.local_execution.installed_models', return_value=[]):
            result = client.get('/runtime-models').json()
            self.assertTrue(result['available'])
            self.assertEqual(result['items'], [])

    def test_showcase_catalog_and_remote_execution_gate(self):
        client = TestClient(create_app('sqlite:///:memory:', enable_local_runs=True), client=('127.0.0.1', 50000))
        catalog = client.get('/showcase-models').json()
        self.assertEqual(len(catalog['items']), 3)
        self.assertFalse(catalog['remote_execution_enabled'])
        response = client.post('/internal/benchmark-jobs', json={
            'model': 'remote-model', 'provider': 'openai-compatible', 'endpoint': 'https://example.test/v1', 'api_key': 'ephemeral'
        }, headers={'X-SecureLLM-Local': '1'})
        self.assertEqual(response.status_code, 403)

    def test_remote_input_never_appears_in_job_response(self):
        client = TestClient(create_app('sqlite:///:memory:', enable_local_runs=True, enable_remote_runs=True), client=('127.0.0.1', 50000))
        with patch('apps.api.local_execution.threading.Thread'):
            response = client.post('/internal/benchmark-jobs', json={
                'model': 'remote-model', 'provider': 'openai-compatible', 'endpoint': 'https://example.test/v1', 'api_key': 'ephemeral'
            }, headers={'X-SecureLLM-Local': '1'})
        self.assertEqual(response.status_code, 202)
        self.assertNotIn('ephemeral', response.text)
        self.assertEqual(response.json()['provider'], 'openai-compatible')
