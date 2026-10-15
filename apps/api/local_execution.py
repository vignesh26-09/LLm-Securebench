"""Explicitly enabled loopback-only execution of installed local models."""
import threading
import uuid
import hashlib
import httpx
from datetime import datetime, timezone
from typing import Literal
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from core.inference.ollama_provider import installed_models
from core.inference.contracts import InferenceError
from core.inference.openai_compatible_provider import normalize_endpoint
from scripts.run_local_benchmark import run_model
from core.dataset.benchmark_catalog import dataset_options, load_selection, EXAMPLE_KEY

SHOWCASE_MODELS = (
    {"id": "gemma3:4b", "name": "Gemma 3 4B", "ollama_model": "gemma3:4b",
     "description": "Open-weight showcase preset for local evaluation.", "access": "Install locally in Ollama to run."},
    {"id": "qwen3.5:2b", "name": "Qwen 3.5 2B", "ollama_model": "qwen3.5:2b",
     "description": "Compact showcase preset for local evaluation.", "access": "Install locally in Ollama to run."},
    {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "ollama_model": "llama3.2:3b",
     "description": "Open-weight showcase preset for local evaluation.", "access": "Install locally in Ollama to run."},
)


class RunInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    model: str = Field(min_length=1, max_length=200)
    provider: Literal['ollama-local', 'openai-compatible'] = 'ollama-local'
    endpoint: str | None = Field(default=None, max_length=1000)
    api_key: str | None = Field(default=None, max_length=2000, repr=False)
    dataset_key: Literal['repository-example', 'mixed-source-10000-v1'] = EXAMPLE_KEY
    case_offset: int = Field(default=0, ge=0)
    case_count: int | None = Field(default=None, ge=1, le=1000)

    @model_validator(mode='after')
    def validate_provider_configuration(self):
        if self.provider == 'ollama-local' and (self.endpoint is not None or self.api_key is not None):
            raise ValueError('Local Ollama runs do not accept an endpoint or API key')
        if self.provider == 'openai-compatible':
            if not self.endpoint:
                raise ValueError('An OpenAI-compatible endpoint is required')
            normalize_endpoint(self.endpoint)
        return self


def register_execution(app, database_url, enabled=False, remote_enabled=False):
    jobs = {}
    lock = threading.Lock()

    @app.post('/internal/model-connections', status_code=201)
    def connect_model(body: RunInput, request: Request):
        from core.persistence.models import ModelConfigEntity
        if request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            raise HTTPException(403, 'Model connection requires a local workspace connection')
        normalized = None
        if body.provider == 'ollama-local':
            try:
                found = next((item for item in installed_models() if item['name'] == body.model), None)
            except InferenceError:
                raise HTTPException(503, 'Ollama is unreachable. Start Ollama and retry.') from None
            if found is None:
                raise HTTPException(422, 'This model is not installed in Ollama. Choose an installed model or install it first.')
            details = {'digest': found.get('digest'), 'details': found.get('details')}
        else:
            if not remote_enabled:
                raise HTTPException(403, 'API model connections are disabled on this server. Local Ollama import is available.')
            normalized = normalize_endpoint(body.endpoint or '')
            models_url = normalized.removesuffix('/chat/completions') + '/models'
            headers = {'Authorization': f'Bearer {body.api_key}'} if body.api_key else {}
            try:
                with httpx.Client(timeout=10, follow_redirects=False) as transport:
                    result = transport.get(models_url, headers=headers)
                if result.status_code != 200:
                    raise HTTPException(422, f'Model listing returned HTTP {result.status_code}. Check endpoint and API key.')
                available = result.json().get('data', [])
                if not any(item.get('id') == body.model for item in available if isinstance(item, dict)):
                    raise HTTPException(422, 'The endpoint did not list this model identifier.')
            except (httpx.HTTPError, ValueError, AttributeError):
                raise HTTPException(422, 'Could not verify the endpoint. Check its URL and connection.') from None
            details = {}
        identity = f'{body.provider}:{body.model}:{normalized or "local"}'
        connection_id = 'connection-' + hashlib.sha256(identity.encode()).hexdigest()[:24]
        with app.state.session_factory() as session:
            saved = session.get(ModelConfigEntity, connection_id)
            payload = {'provider': body.provider, 'endpoint': normalized, 'connection_verified': True, **details}
            if saved is None:
                session.add(ModelConfigEntity(id=connection_id, model_name=body.model, payload=payload))
            else:
                saved.payload = payload
            session.commit()
        return {'id': connection_id, 'model': body.model, 'provider': body.provider, 'endpoint': normalized,
                'verified': True, 'message': 'Connection verified and saved. Run a benchmark to evaluate behavior.'}

    @app.get('/runtime-models')
    def runtime_models():
        try:
            return {'available': True, 'execution_enabled': enabled, 'items': installed_models()}
        except InferenceError:
            return {'available': False, 'execution_enabled': enabled, 'items': [],
                    'reason': 'Start the local Ollama service to discover installed models.'}

    @app.get('/showcase-models')
    def showcase_models():
        return {'items': list(SHOWCASE_MODELS), 'remote_execution_enabled': remote_enabled,
                'note': 'Showcase entries are presets, not claims that a model is installed, tested, or scientifically validated.'}

    @app.get('/benchmark-datasets')
    def benchmark_datasets():
        return {'items': dataset_options(),
                'note': 'Corpus size is source-input availability, not completed evaluations or validated safety evidence.'}

    @app.get('/benchmark-jobs')
    def list_jobs():
        with lock:
            return {'items': [dict(job) for job in reversed(list(jobs.values()))]}

    @app.get('/benchmark-jobs/{job_id}')
    def get_job(job_id: str):
        with lock:
            job = jobs.get(job_id)
            if job is None:
                raise HTTPException(404, 'Benchmark job not found in this server session')
            return dict(job)

    def execute(job_id, run_spec):
        def progress(stage, **details):
            with lock:
                jobs[job_id].update(stage=stage, **details)
        try:
            result = run_model(database_url=database_url, run_id=job_id, progress_callback=progress, **run_spec)
            with lock:
                jobs[job_id].update(status=result['status'], stage='Completed and persisted', result=result,
                                    completed_at=datetime.now(timezone.utc).isoformat())
        except Exception:
            with lock:
                jobs[job_id].update(status='failed', stage='Failed before persistence', completed_at=datetime.now(timezone.utc).isoformat(),
                                    error='Execution or persistence failed. Inspect local service logs and saved run artifacts.')

    @app.post('/internal/benchmark-jobs', status_code=202)
    def create_job(body: RunInput, request: Request):
        if not enabled:
            raise HTTPException(403, 'Local benchmark execution is disabled')
        if request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            raise HTTPException(403, 'Local execution requires a loopback connection')
        if request.headers.get('X-SecureLLM-Local') != '1' or request.headers.get('origin') not in {
            None, 'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8000'}:
            raise HTTPException(403, 'Invalid local execution request')
        if body.provider == 'ollama-local':
            try:
                names = {model['name'] for model in installed_models()}
            except InferenceError:
                raise HTTPException(503, 'Local Ollama is unreachable')
            if body.model not in names:
                raise HTTPException(422, 'Choose an installed model')
        if body.provider == 'openai-compatible' and not remote_enabled:
            raise HTTPException(403, 'Remote model execution is disabled on this server')
        try:
            selection = load_selection(body.dataset_key, offset=body.case_offset,
                                       count=body.case_count)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        with lock:
            if any(job['status'] == 'running' for job in jobs.values()):
                raise HTTPException(409, 'A local benchmark is already running')
            while len(jobs) >= 50:
                del jobs[next(iter(jobs))]
            job_id = uuid.uuid4().hex
            jobs[job_id] = {'id': job_id, 'model': body.model, 'provider': body.provider,
                            'dataset_key': selection.key, 'case_offset': selection.offset,
                            'case_count': selection.count, 'source_count': selection.source_count,
                            'status': 'running',
                            'stage': 'Job accepted; preparing benchmark source', 'submitted_at': datetime.now(timezone.utc).isoformat()}
            result = dict(jobs[job_id])
        run_spec = {'model_name': body.model, 'provider_kind': body.provider,
                    'dataset_key': selection.key, 'case_offset': selection.offset,
                    'case_count': selection.count}
        if body.provider == 'openai-compatible':
            run_spec.update(endpoint=body.endpoint, api_key=body.api_key)
        threading.Thread(target=execute, args=(job_id, run_spec), daemon=True).start()
        return result
