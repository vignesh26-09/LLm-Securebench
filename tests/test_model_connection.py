import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select
from apps.api.main import create_app
from core.persistence.models import ModelConfigEntity


class ModelConnectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app(f"sqlite:///{Path(self.directory.name) / 'models.db'}", require_auth=True, enable_remote_runs=True)
        self.client = TestClient(self.app, client=('127.0.0.1', 50010))

    def tearDown(self):
        self.app.state.session_factory.kw['bind'].dispose()
        self.directory.cleanup()

    def test_guest_cannot_import_and_sample_can_verify_installed_model(self):
        payload = {'model': 'custom:1b', 'provider': 'ollama-local'}
        self.assertEqual(self.client.post('/internal/model-connections', json=payload).status_code, 401)
        self.assertEqual(self.client.post('/auth/sample').status_code, 200)
        with patch('apps.api.local_execution.installed_models', return_value=[{'name': 'custom:1b', 'digest': 'digest'}]):
            response = self.client.post('/internal/model-connections', json=payload)
            self.assertEqual(response.status_code, 201)
            self.assertTrue(response.json()['verified'])
            second = self.client.post('/internal/model-connections', json=payload)
            self.assertEqual(second.json()['id'], response.json()['id'])
        with self.app.state.session_factory() as session:
            row = session.scalar(select(ModelConfigEntity))
            self.assertEqual(row.model_name, 'custom:1b')
            self.assertTrue(row.payload['connection_verified'])
        with patch('apps.api.local_execution.installed_models', return_value=[]):
            self.assertEqual(self.client.post('/internal/model-connections', json=payload).status_code, 422)

    def test_remote_verification_never_persists_api_key(self):
        self.client.post('/auth/sample')
        transport = MagicMock()
        transport.__enter__.return_value = transport
        transport.get.return_value = httpx.Response(200, json={'data': [{'id': 'custom-model'}]})
        with patch('apps.api.local_execution.httpx.Client', return_value=transport):
            response = self.client.post('/internal/model-connections', json={'model': 'custom-model', 'provider': 'openai-compatible', 'endpoint': 'https://example.test/v1', 'api_key': 'test-ephemeral-key'})
        self.assertEqual(response.status_code, 201)
        with self.app.state.session_factory() as session:
            row = session.scalar(select(ModelConfigEntity))
            self.assertNotIn('test-ephemeral-key', str(row.payload))
            self.assertNotIn('api_key', row.payload)
        self.assertNotIn('test-ephemeral-key', response.text)

    def test_bad_remote_model_is_rejected(self):
        self.client.post('/auth/sample')
        transport = MagicMock()
        transport.__enter__.return_value = transport
        transport.get.return_value = httpx.Response(200, json={'data': [{'id': 'different-model'}]})
        with patch('apps.api.local_execution.httpx.Client', return_value=transport):
            response = self.client.post('/internal/model-connections', json={'model': 'missing-model', 'provider': 'openai-compatible', 'endpoint': 'https://example.test/v1'})
        self.assertEqual(response.status_code, 422)
