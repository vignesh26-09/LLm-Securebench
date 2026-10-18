import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from apps.api.main import create_app
from apps.api.resources import RESOURCES
from core.persistence.models import ModelConfigEntity, BenchmarkRunEntity, EvaluationResultEntity, LayerTwoResultEntity, ScientificRecordEntity
from scripts.import_repository_data import import_example
from scripts.analyze_repository_example import analyze_example


class ResourceApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("sqlite:///:memory:")
        self.client = TestClient(self.app)
        self.factory = self.app.state.session_factory

    def test_all_resources_are_read_only_paginated_and_have_not_found(self):
        for resource in RESOURCES:
            with self.subTest(resource=resource):
                self.assertEqual(self.client.get('/' + resource).json(), {"items": [], "total": 0, "limit": 25, "offset": 0})
                self.assertEqual(self.client.get('/' + resource + '/absent').status_code, 404)
                for method in ('post', 'put', 'patch', 'delete'):
                    self.assertEqual(getattr(self.client, method)('/' + resource).status_code, 405)
                for query in ('limit=101', 'offset=-1', 'sort=payload', 'direction=invalid', 'filter_by=payload&value=x', 'value=x'):
                    self.assertEqual(self.client.get('/' + resource + '?' + query).status_code, 422)

    def test_links_nulls_redaction_and_pagination(self):
        with self.factory.begin() as session:
            session.add_all([ModelConfigEntity(id='a', model_name='Test fixture', payload={'api_key': 'private', 'nested': {'token': 'private'}, 'temperature': None}), ModelConfigEntity(id='b', model_name='Other fixture')])
            session.flush()
            session.add(BenchmarkRunEntity(id='r', model_config_id='a', status='fixture'))
            session.flush()
            session.add(EvaluationResultEntity(id='e', benchmark_run_id='r', execution_status='failed', response=None, provider_metadata={'password': 'private'}))
            session.flush()
            session.add(LayerTwoResultEntity(id='l', evaluation_result_id='e', dimension='fixture', status='skipped', score=None, confidence=None, payload={'score': None}))
        page = self.client.get('/models?limit=1&sort=id&direction=desc').json()
        self.assertEqual(page['total'], 2)
        self.assertEqual(page['items'][0]['id'], 'b')
        model = self.client.get('/models/a').json()
        self.assertNotIn('private', str(model))
        self.assertIsNone(model['payload']['temperature'])
        self.assertEqual(self.client.get('/benchmark-runs?filter_by=model_config_id&value=a').json()['total'], 1)
        self.assertEqual(self.client.get('/models?filter_by=id&value=%27%20OR%201=1').json()['total'], 0)
        layer = self.client.get('/layer2-results?filter_by=evaluation_result_id&value=e').json()['items'][0]
        self.assertIsNone(layer['score'])
        self.assertEqual(layer['status'], 'skipped')
        self.assertNotIn('private', self.client.get('/evaluations/e').text)
        self.assertEqual(self.client.get('/dashboard-summary').json()['counts']['models'], 2)

    def test_source_import_is_lossless_and_idempotent(self):
        with self.factory() as session:
            first = import_example(session)
            second = import_example(session)
        self.assertTrue(first['imported'])
        self.assertFalse(second['imported'])
        self.assertEqual(first['source_records'], 3)
        result = self.client.get('/dataset-versions').json()['items'][0]
        self.assertEqual(result['content_hash'], first['sha256'])
        self.assertEqual(len(result['payload']['records']), 3)
        self.assertTrue(result['payload']['records'][0]['prompt'].startswith('  '))
        self.assertEqual(self.client.get('/dashboard-summary').json()['counts']['scientific-records'], 0)

    def test_database_failure_is_safe(self):
        with patch('sqlalchemy.orm.Session.scalar', side_effect=OperationalError('secret SQL', {}, Exception('private'))):
            response = self.client.get('/models')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', response.text)
        self.assertIn('X-Request-ID', response.headers)

    def test_dqi_uses_existing_example_and_is_explicitly_exploratory(self):
        with self.factory() as session:
            import_example(session)
            first = analyze_example(session)
            second = analyze_example(session)
        self.assertTrue(first['created'])
        self.assertFalse(second['created'])
        record = self.client.get('/scientific-records/' + first['id']).json()
        self.assertEqual(record['scope'], 'DATASET_VERSION')
        self.assertFalse(record['provenance']['scientifically_validated'])
        self.assertFalse(record['provenance']['embeddings_supplied'])
        self.assertIsNone(record['payload']['components']['novelty'])
        self.assertIsNone(record['payload']['score'])
        self.assertEqual(record['payload']['status'], 'unavailable')
        self.assertEqual(record['provenance']['record_count'], 3)
        self.assertEqual(self.client.get('/models').json()['total'], 0)

    def test_scientific_detail_preserves_scope_provenance_and_null(self):
        with self.factory.begin() as session:
            session.add(ScientificRecordEntity(id='rc-fixture', family='rc', schema_version='lossless-payload-v1',
                scope='SESSION_SEQUENCE', owner_id='sequence-fixture', status='undefined',
                payload={'value': None}, provenance={'kind': 'test_fixture'}))
        result = self.client.get('/scientific-records/rc-fixture').json()
        self.assertEqual(result['owner_id'], 'sequence-fixture')
        self.assertEqual(result['payload'], {'value': None})
        self.assertEqual(result['provenance'], {'kind': 'test_fixture'})
        self.assertEqual(self.client.get('/scientific-records/missing').status_code, 404)

    def test_research_evidence_endpoint_is_read_only_and_family_scoped(self):
        with self.factory.begin() as session:
            session.add_all([
                ScientificRecordEntity(id='pre-fixture', family='preregistration', schema_version='preregistration-v1',
                    scope='EXPERIMENT', owner_id='experiment', status='locked', payload={'version': 1}, provenance={}),
                ScientificRecordEntity(id='other-fixture', family='dqi', schema_version='v1',
                    scope='DATASET_VERSION', owner_id='dataset', status='unavailable', payload={}, provenance={}),
            ])
        response = self.client.get('/research-evidence/preregistration')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['family'], 'preregistration')
        self.assertEqual([item['id'] for item in response.json()['items']], ['pre-fixture'])
        self.assertEqual(self.client.get('/research-evidence/not-a-family').status_code, 404)
        self.assertEqual(self.client.post('/research-evidence/preregistration').status_code, 405)
