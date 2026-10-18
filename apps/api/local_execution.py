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
from core.dataset.benchmark_catalog import dataset_options, load_selection, LARGE_KEY
from core.dataset.sample_rotation import PILOT_CASES, QUICK_CASES, allocate_pilot, allocate_rotating

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
    dataset_key: Literal['repository-example', 'mixed-source-10000-v1'] = LARGE_KEY
    case_offset: int = Field(default=0, ge=0)
    case_count: int = Field(default=10000, ge=1, le=10000)
    judge_model: str | None = Field(default=None, min_length=1, max_length=200)
    context_window: int = Field(default=4096, ge=1024, le=65536)
    confirm_full_corpus: bool = False
    resume_run_id: str | None = Field(default=None, pattern=r'^[a-zA-Z0-9]{1,64}$')

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
    stop_events = {}
    lock = threading.Lock()

    def persisted_jobs(job_id=None):
        from sqlalchemy import select, func
        from core.persistence.models import BenchmarkRunEntity, ModelConfigEntity, EvaluationResultEntity
        with app.state.session_factory() as session:
            statement = select(BenchmarkRunEntity).order_by(BenchmarkRunEntity.created_at.desc()).limit(50)
            if job_id:
                statement = select(BenchmarkRunEntity).where(BenchmarkRunEntity.id == job_id)
            output = []
            for saved in session.scalars(statement):
                config = session.get(ModelConfigEntity, saved.model_config_id)
                if config is None or config.payload.get('protocol') not in {'full-corpus-controlled-v1', 'quick-response-check-v1'}:
                    continue
                quick = config.payload.get('protocol') == 'quick-response-check-v1'
                count = session.scalar(select(func.count()).select_from(EvaluationResultEntity).where(
                    EvaluationResultEntity.benchmark_run_id == saved.id))
                interrupted = saved.status not in {'completed', 'completed_with_errors', 'stopped'}
                planned = saved.payload.get('planned_cases', 10000)
                output.append({'id': saved.id, 'model': config.model_name,
                    'provider': config.payload['provider'], 'judge_model': config.payload.get('judge_model'),
                    'context_window': config.payload.get('context_window'), 'dataset_key': LARGE_KEY,
                    'case_offset': 0, 'case_count': planned, 'source_count': 10000,
                    'sample_mode': f'rotating_quick_{planned}' if quick else 'balanced_rotating_50' if planned == PILOT_CASES else 'full_corpus',
                    'status': 'interrupted' if interrupted else saved.status,
                    'stage': ('Server stopped; resume this saved run' if interrupted else
                              'Stopped by user; saved work can be resumed' if saved.status == 'stopped' else 'Completed and persisted'),
                    'error': 'Saved observations and committed cases are retained. Resume with the same configuration.' if interrupted else None,
                    'submitted_at': saved.created_at.isoformat(), 'completed_cases': count,
                    'total_cases': planned, 'planned_target_calls': planned * 10, 'planned_judge_calls': planned * 20})
            return output

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
            live = [dict(job) for job in reversed(list(jobs.values()))]
        ids = {job['id'] for job in live}
        return {'items': live + [job for job in persisted_jobs() if job['id'] not in ids]}

    @app.get('/benchmark-jobs/{job_id}')
    def get_job(job_id: str):
        with lock:
            job = jobs.get(job_id)
            if job is not None:
                return dict(job)
        saved = persisted_jobs(job_id)
        if saved:
            return saved[0]
        raise HTTPException(404, 'Benchmark job not found')

    def execute(job_id, run_spec):
        def progress(stage, **details):
            with lock:
                jobs[job_id].update(stage=stage, **details)
        try:
            result = run_model(database_url=database_url, run_id=job_id, progress_callback=progress,
                               stop_requested=stop_events[job_id].is_set, **run_spec)
            with lock:
                jobs[job_id].update(status=result['status'],
                                    stage='Stopped by user; saved work can be resumed' if result['status'] == 'stopped' else 'Completed and persisted', result=result,
                                    completed_at=datetime.now(timezone.utc).isoformat())
        except Exception:
            with lock:
                jobs[job_id].update(status='failed', stage='Failed before persistence', completed_at=datetime.now(timezone.utc).isoformat(),
                                    error='Execution interrupted. Committed case results and controlled observations are retained. Resume with the same run ID and configuration.')
        finally:
            with lock:
                stop_events.pop(job_id, None)

    @app.post('/internal/benchmark-jobs/{job_id}/stop')
    def stop_job(job_id: str, request: Request):
        if request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            raise HTTPException(403, 'Stopping a benchmark requires a local workspace connection')
        if request.headers.get('X-SecureLLM-Local') != '1':
            raise HTTPException(403, 'Invalid local stop request')
        with lock:
            job = jobs.get(job_id)
            if job is None:
                raise HTTPException(404, 'Active benchmark job not found on this server')
            if job['case_count'] == QUICK_CASES:
                raise HTTPException(409, 'Quick checks finish after ten bounded calls and cannot be resumed.')
            if getattr(request.state, 'guest_stop', False) and (job['provider'] != 'ollama-local' or job['model'] not in
                    {item['ollama_model'] for item in SHOWCASE_MODELS}):
                raise HTTPException(401, 'Sign in to stop a custom-model run')
            if job['status'] == 'stopping':
                return dict(job)
            if job['status'] != 'running' or job_id not in stop_events:
                raise HTTPException(409, 'This benchmark is no longer running')
            stop_events[job_id].set()
            job.update(status='stopping', stage='Stop requested; finishing the current model call and retaining saved evidence')
            return dict(job)

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
        if body.dataset_key != LARGE_KEY or body.case_offset != 0 or body.case_count not in {QUICK_CASES, PILOT_CASES, 10000}:
            raise HTTPException(422, 'Choose a ten-prompt quick check, rotating 50-prompt pilot, or all 10,000 prompts.')
        if body.case_count == 10000 and not body.confirm_full_corpus:
            raise HTTPException(422, 'Confirm the full run budget: 100,000 target calls plus up to 200,000 local judge calls.')
        quick = body.case_count == QUICK_CASES
        judge_model = None if quick else body.judge_model or body.model
        if not quick:
            try:
                judge_names = {model['name'] for model in installed_models()}
            except InferenceError:
                raise HTTPException(503, 'Local Ollama judge is unreachable') from None
            if judge_model not in judge_names:
                raise HTTPException(422, 'Choose an installed local judge model. No models are downloaded automatically.')
        try:
            selection = load_selection(body.dataset_key, offset=body.case_offset,
                                       count=10000)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        with lock:
            if any(job['status'] in {'running', 'stopping'} for job in jobs.values()):
                raise HTTPException(409, 'A local benchmark is already running')
            while len(jobs) >= 50:
                del jobs[next(iter(jobs))]
            job_id = body.resume_run_id or uuid.uuid4().hex
            sample_indices = None
            sample_cycle = None
            if body.resume_run_id:
                if quick:
                    raise HTTPException(422, 'Quick checks cannot be resumed; start a new rotating sample.')
                from core.persistence.models import BenchmarkRunEntity, ModelConfigEntity
                with app.state.session_factory() as session:
                    saved = session.get(BenchmarkRunEntity, job_id)
                    config = session.get(ModelConfigEntity, saved.model_config_id) if saved else None
                    if saved is None or config is None or config.model_name != body.model or config.payload.get('protocol') != 'full-corpus-controlled-v1':
                        raise HTTPException(422, 'Resume requires an existing full-corpus run for this model.')
                    if saved.payload.get('planned_cases', 10000) != body.case_count or config.payload.get('judge_model') != judge_model or config.payload.get('context_window') != body.context_window or config.payload.get('provider') != body.provider:
                        raise HTTPException(422, 'Resume requires the original case count, judge, provider and context settings.')
                    sample_indices = saved.payload.get('sample_indices')
                    sample_cycle = saved.payload.get('sample_cycle')
                    if body.case_count == PILOT_CASES and (not isinstance(sample_indices, list) or len(sample_indices) != PILOT_CASES):
                        raise HTTPException(422, 'Saved pilot allocation is unavailable for resume.')
            elif body.case_count in {QUICK_CASES, PILOT_CASES}:
                from sqlalchemy import select
                from core.persistence.models import ScientificRecordEntity
                with app.state.session_factory() as session, session.begin():
                    prior = [row.payload for row in session.scalars(select(ScientificRecordEntity).where(
                        ScientificRecordEntity.family == 'benchmark_sample_allocation'))
                        if row.payload.get('source_sha256') == selection.source_sha256]
                    allocated = allocate_rotating(selection, prior, 5) if quick else allocate_pilot(selection, prior)
                    sample_indices = list(allocated.indices)
                    sample_cycle = allocated.cycle
                    session.add(ScientificRecordEntity(id=f'{job_id}:sample-allocation',
                        family='benchmark_sample_allocation', schema_version='rotating-quick-10-v1' if quick else 'balanced-rotating-50-v1',
                        scope='BENCHMARK_RUN', owner_id=job_id, status='assigned',
                        payload={'sample_indices': sample_indices, 'sample_cycle': sample_cycle,
                                 'selection_sha256': allocated.selection_sha256,
                                 'source_sha256': selection.source_sha256},
                        provenance={'reporting_class': 'engineering_only',
                                    'scientifically_validated': False, 'assignment': 'without_replacement_within_cycle'}))
            jobs[job_id] = {'id': job_id, 'model': body.model, 'provider': body.provider,
                            'dataset_key': selection.key, 'case_offset': selection.offset,
                            'case_count': body.case_count, 'source_count': selection.source_count,
                            'judge_model': judge_model, 'context_window': body.context_window, 'total_cases': body.case_count, 'completed_cases': 0,
                            'sample_mode': 'rotating_quick_10' if quick else 'balanced_rotating_50' if body.case_count == PILOT_CASES else 'full_corpus',
                            'planned_target_calls': body.case_count if quick else body.case_count * 10,
                            'planned_judge_calls': 0 if quick else body.case_count * 20,
                            'status': 'running',
                            'stage': 'Job accepted; preparing benchmark source', 'submitted_at': datetime.now(timezone.utc).isoformat()}
            stop_events[job_id] = threading.Event()
            result = dict(jobs[job_id])
        run_spec = {'model_name': body.model, 'provider_kind': body.provider,
                    'dataset_key': selection.key, 'case_offset': selection.offset,
                    'case_count': body.case_count, 'full_corpus': not quick,
                    'judge_model': judge_model, 'context_window': body.context_window,
                    'sample_indices': sample_indices, 'sample_cycle': sample_cycle}
        if body.provider == 'openai-compatible':
            run_spec.update(endpoint=body.endpoint, api_key=body.api_key)
        threading.Thread(target=execute, args=(job_id, run_spec), daemon=True).start()
        return result
