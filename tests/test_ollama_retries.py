import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient
from apps.api.main import create_app
from core.inference.contracts import InferenceRequest
from core.inference.ollama_provider import OllamaProvider, ollama_timeout
from core.models.registry import ModelMetadata
from scripts.run_local_benchmark import run_model


def response():
    return io.BytesIO(json.dumps({'done': True, 'response': 'Synthetic unit test answer'}).encode())


def test_success_default_timeout_and_environment_override(monkeypatch):
    monkeypatch.delenv('SECURELLM_OLLAMA_TIMEOUT_SECONDS', raising=False)
    assert ollama_timeout() == 120
    monkeypatch.setenv('SECURELLM_OLLAMA_TIMEOUT_SECONDS', '240')
    with patch('core.inference.ollama_provider.urlopen', return_value=response()) as call:
        result = OllamaProvider().generate(InferenceRequest(ModelMetadata('fake', 'ollama-local'), 'Fake test'))
    assert result.text == 'Synthetic unit test answer'
    assert call.call_args.kwargs['timeout'] == 240


@pytest.mark.parametrize('failure', [TimeoutError('timeout'), URLError(ConnectionRefusedError('offline'))])
def test_retry_then_success(failure):
    with patch('core.inference.ollama_provider.urlopen', side_effect=[failure, failure, response()]) as call, patch('core.inference.ollama_provider.sleep') as sleep:
        result = OllamaProvider().generate(InferenceRequest(ModelMetadata('fake', 'ollama-local'), 'Fake test'))
    assert result.text
    assert call.call_count == 3
    assert [args.args[0] for args in sleep.call_args_list] == [1, 2]


def test_http_errors_are_not_retried():
    with patch('core.inference.ollama_provider.urlopen', side_effect=HTTPError('http://localhost', 500, 'error', {}, None)) as call:
        with pytest.raises(Exception, match='HTTP 500'):
            OllamaProvider().generate(InferenceRequest(ModelMetadata('fake', 'ollama-local'), 'Fake test'))
    assert call.call_count == 1


def test_final_failure_is_saved_without_safe_results():
    with tempfile.TemporaryDirectory() as directory:
        url = f'sqlite:///{Path(directory) / "test.db"}'
        app = create_app(url)
        with patch('core.inference.ollama_provider.urlopen', side_effect=TimeoutError('offline')) as call, patch('core.inference.ollama_provider.sleep'):
            outcome = run_model('fake', database_url=url, inventory=[{'name': 'fake', 'digest': 'fake-digest'}], output_directory=Path(directory)/'runs')
        report = TestClient(app).get(f'/benchmark-runs/{outcome["run_id"]}/report').json()
        assert call.call_count == 9  # Three cases, each with three attempts.
        assert len(report['cases']) == 3
        assert all(case['execution_status'] == 'failed' for case in report['cases'])
        assert all(not case['response_available'] for case in report['cases'])
        from sqlalchemy.orm import Session
        from core.persistence.models import EvaluationResultEntity, LayerOneResultEntity
        with Session(app.state.session_factory.kw['bind']) as session:
            assert all('timed out' in item.provider_metadata['error'] for item in session.query(EvaluationResultEntity))
            assert session.query(LayerOneResultEntity).count() == 0
        app.state.session_factory.kw['bind'].dispose()
