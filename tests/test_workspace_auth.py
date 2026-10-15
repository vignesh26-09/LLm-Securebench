"""Account boundaries and public preset access."""
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from apps.api.main import create_app


class WorkspaceAuthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.directory.name) / 'accounts.db'}"
        self.app = create_app(self.url, require_auth=True)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.state.session_factory.kw['bind'].dispose()
        self.directory.cleanup()

    def test_account_session_and_logout(self):
        self.assertEqual(self.client.get('/dashboard-summary').status_code, 401)
        payload = {'email': 'Test@example.test', 'name': 'Tester', 'password': 'a-long-test-password'}
        response = self.client.post('/auth/register', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertEqual(self.client.get('/auth/session').json()['user']['email'], 'test@example.test')
        self.assertEqual(self.client.get('/dashboard-summary').status_code, 200)
        self.assertEqual(self.client.post('/auth/logout').status_code, 200)
        self.assertIsNone(self.client.get('/auth/session').json()['user'])
        self.assertEqual(self.client.get('/dashboard-summary').status_code, 401)
        self.assertEqual(self.client.post('/auth/login', json={**payload, 'password': 'wrong-password'}).status_code, 401)
        self.assertEqual(self.client.post('/auth/login', json=payload).status_code, 200)
        engine = create_engine(self.url)
        with engine.connect() as connection:
            saved = connection.execute(text('SELECT password_hash FROM workspace_users')).scalar()
        engine.dispose()
        self.assertNotEqual(saved, payload['password'])
        self.assertEqual(len(saved), 64)

    def test_public_presets_and_custom_model_gate(self):
        self.assertEqual(self.client.get('/showcase-models').status_code, 200)
        preset = {'model': 'gemma3:4b', 'provider': 'ollama-local', 'case_count': 10000, 'dataset_key': 'mixed-source-10000-v1', 'confirm_full_corpus': True}
        # The request passes authentication and reaches the disabled execution gate.
        result = self.client.post('/internal/benchmark-jobs', json=preset)
        self.assertEqual(result.status_code, 403)
        self.assertIn('execution is disabled', result.json()['detail'])
        self.assertEqual(self.client.post('/internal/benchmark-jobs', json={**preset, 'model': 'custom:model'}).status_code, 401)
        self.assertEqual(self.client.post('/internal/benchmark-jobs', json={**preset, 'case_count': 100}).status_code, 422)
        self.assertEqual(self.client.post('/auth/register', json={'email': 'a@b.test', 'password': 'test-password'}, headers={'Origin': 'https://untrusted.example'}).status_code, 403)

    def test_duplicate_account_and_expiry(self):
        payload = {'email': 'same@example.test', 'password': 'long-password'}
        self.assertEqual(self.client.post('/auth/register', json=payload).status_code, 200)
        self.assertEqual(self.client.post('/auth/register', json=payload).status_code, 409)
        engine = create_engine(self.url)
        with engine.begin() as conn:
            conn.execute(text('UPDATE workspace_sessions SET expires = 0'))
        engine.dispose()
        self.assertIsNone(self.client.get('/auth/session').json()['user'])
        self.assertEqual(self.client.get('/dashboard-summary').status_code, 401)

    def test_sample_signin_is_local_and_creates_real_session(self):
        self.assertEqual(self.client.post('/auth/sample').status_code, 403)
        with TestClient(self.app, client=('127.0.0.1', 50010)) as local:
            result = local.post('/auth/sample')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['user']['name'], 'Sample Researcher')
            self.assertEqual(local.get('/dashboard-summary').status_code, 200)
            self.assertEqual(local.post('/auth/logout').status_code, 200)
            self.assertIsNone(local.get('/auth/session').json()['user'])
