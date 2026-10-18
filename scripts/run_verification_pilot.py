"""Run installed-model smoke checks, gate, then resumable controlled pilots.

Fresh: python scripts/run_verification_pilot.py --output <new directory>
Pilot/resume: python scripts/run_verification_pilot.py --resume <directory> --pilot
Only installed models are used. Results and checkpoints stay outside Git.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import random
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.dataset.benchmark_catalog import LARGE_KEY, load_selection
from core.dataset.sample_rotation import CATEGORIES
from core.inference.ollama_provider import installed_models, ollama_timeout
from core.persistence.database import make_engine
from core.persistence.models import BenchmarkRunEntity, EvaluationResultEntity
from scripts.run_local_benchmark import run_model
from scripts.run_full_benchmark import run_full_model

MODELS = ('gemma3:4b','qwen3.5:2b','llama3.2:3b')


def atomic_json(path, value):
    temporary = path.with_suffix('.pending')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
    for attempt in range(6):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.05 * (2 ** attempt))


def check_gate(smoke):
    return len(smoke) == 3 and all(row['completed'] == 10 and row['failed'] == 0 for row in smoke)


def allocate(selection, count, seed):
    chooser=random.Random(seed)
    return sorted(index for category in CATEGORIES for index in chooser.sample(
        [i for i,row in enumerate(selection.dataset.records) if row.category == category],count//2))


def summarize_run(engine, run_id, model):
    with Session(engine) as session:
        rows=session.scalars(select(EvaluationResultEntity).where(EvaluationResultEntity.benchmark_run_id==run_id)).all()
        times=[row.latency_ms for row in rows if row.execution_status=='completed' and row.latency_ms is not None]
        failed=[{'case_id':row.case_id,'status':row.execution_status,'error':row.provider_metadata.get('error') or ('Empty visible model output' if not row.response or not row.response.strip() else 'Controlled response failure; inspect saved observation reason')} for row in rows if row.execution_status!='completed' or not row.response or not row.response.strip()]
        return {'model':model,'run_id':run_id,'completed':sum(row.execution_status=='completed' and bool(row.response and row.response.strip()) for row in rows),
            'failed':len(failed),'avg_latency_ms':sum(times)/len(times) if times else None,'failure_reasons':failed}


def execute(folder, *, resume=False, pilot=False):
    metadata_path=folder/'run_metadata.json'
    inventory=installed_models()
    versions={row['name']:row['digest'] for row in inventory if row['name'] in MODELS}
    if set(versions)!=set(MODELS):
        raise RuntimeError('Required installed models are unavailable; downloads are forbidden')
    selection=load_selection(LARGE_KEY,count=10000)
    if resume:
        metadata=json.loads(metadata_path.read_text())
        if metadata['model_digests']!=versions or metadata['prompt_set_sha256']!=selection.source_sha256 or metadata['timeout_seconds']!=ollama_timeout():
            raise ValueError('Resume model digests, prompt set or timeout differ from frozen metadata')
    else:
        folder.mkdir(parents=True,exist_ok=False)
        metadata={'start_time':datetime.now(timezone.utc).isoformat(),'temperature':0,'seed':2026,
            'model_digests':versions,'prompt_set_version':selection.version_id,'prompt_set_sha256':selection.source_sha256,
            'judge_model':'gemma3:4b','judge_digest':versions['gemma3:4b'],'judge_validated':False,
            'timeout_seconds':ollama_timeout(),'transport_max_retries':2,'context_window':4096,
            'smoke_max_new_tokens':64,'pilot_max_new_tokens':128,'judge_max_new_tokens':384,
            'smoke_indices':allocate(selection,10,2026),'pilot_indices':allocate(selection,50,2026),
            'smoke_run_ids':{m:uuid.uuid4().hex for m in MODELS},'pilot_run_ids':{m:uuid.uuid4().hex for m in MODELS}}
        atomic_json(metadata_path,metadata)
    logging.basicConfig(filename=folder/'progress.log',level=logging.INFO,format='%(asctime)s %(message)s',force=True)
    state_path=folder/'state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {'smoke':[],'pilot':[],'phase_errors':[]}
    if len(state['phase_errors'])>=2:
        raise RuntimeError('Phase 3 already failed twice: '+state['phase_errors'][-1])
    state['runner_status']='running'
    atomic_json(state_path,state)
    engine=make_engine(f'sqlite:///{ROOT / "securellmbench.db"}')
    def progress(stage,**details):
        logging.info('%s %s',stage,json.dumps(details))
        state['progress']={'stage':stage,**details,'updated_at':datetime.now(timezone.utc).isoformat()}
        atomic_json(state_path,state)
    try:
        for model in MODELS:
            if any(row['model']==model for row in state['smoke']):
                continue
            rid=metadata['smoke_run_ids'][model]
            with Session(engine) as session:
                saved=session.get(BenchmarkRunEntity,rid)
            if saved is None:
                run_model(model,run_id=rid,dataset_key=LARGE_KEY,case_count=10,
                    sample_indices=tuple(metadata['smoke_indices']),sample_cycle=0,
                    output_directory=folder/'smoke',progress_callback=progress)
            state['smoke'].append(summarize_run(engine,rid,model));atomic_json(state_path,state)
        print('| model | responses/10 | failed | avg latency |',flush=True)
        print('|---|---:|---:|---:|',flush=True)
        for row in state['smoke']:
            latency=f"{row['avg_latency_ms']/1000:.2f}s" if row['avg_latency_ms'] is not None else 'unavailable'
            print(f"| {row['model']} | {row['completed']}/10 | {row['failed']} | {latency} |",flush=True)
        if not check_gate(state['smoke']):
            state['gate']='failed';atomic_json(state_path,state)
            raise RuntimeError('Smoke gate failed: '+json.dumps([row for row in state['smoke'] if row['failed']]))
        state['gate']='passed';atomic_json(state_path,state)
        if not pilot:
            return
        for model in MODELS:
            if any(row['model']==model for row in state['pilot']):
                continue
            progress('Starting/resuming pilot',model=model)
            run_full_model(model,run_id=metadata['pilot_run_ids'][model],judge_model=metadata['judge_model'],
                sample_indices=tuple(metadata['pilot_indices']),sample_cycle=0,context_window=metadata['context_window'],
                output_directory=folder/'pilot',progress_callback=progress)
            state['pilot'].append(summarize_run(engine,metadata['pilot_run_ids'][model],model));atomic_json(state_path,state)
        state['runner_status']='completed'
        state['finished_at']=datetime.now(timezone.utc).isoformat();atomic_json(state_path,state)
        print(json.dumps({'pilot':state['pilot'],'results_folder':str(folder)}),flush=True)
    except Exception as error:
        state['runner_status']='failed'
        state['phase_errors'].append(f'{type(error).__name__}: {error}');atomic_json(state_path,state)
        logging.exception('Phase 3 stopped')
        raise
    finally:
        engine.dispose()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--resume',type=Path)
    parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args()
    execute((args.output or args.resume).resolve(),resume=args.resume is not None,pilot=args.pilot)
