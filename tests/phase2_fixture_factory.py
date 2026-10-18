"""Materialize six explicitly fictional rows; never reads private research data."""
import hashlib
import json
from dataclasses import fields, MISSING
from pathlib import Path
from core.experiments.models import ExperimentalObservation
from scripts.prepare_phase5_annotation import prepare


def materialize(root):
    phase4 = root / 'experiments/phase4'
    observations = phase4 / 'jbb_pilot_run_v1/observations'
    restricted = phase4 / 'restricted_annotation'
    observations.mkdir(parents=True)
    restricted.mkdir()
    def write(path, data):
        path.write_text(json.dumps(data, sort_keys=True, indent=2)+'\n',encoding='utf8')
        return hashlib.sha256(path.read_bytes()).hexdigest()
    sha=write(phase4/'jbb_pilot_dataset_v1.json',{'synthetic_fixture': True, 'records': []})
    specsha=write(phase4/'jbb_pilot_specification_v1.json',{'synthetic_fixture': True,'dataset_hash':sha})
    write(phase4/'jbb_pilot_local_lock_v1.json',{'synthetic_fixture':True,'dataset_sha256':sha,'specification_sha256':specsha})
    seed_rows=json.loads((Path(__file__).parent/'fixtures/annotation_fallback/rows.json').read_text())['rows']
    candidates=[]; items=[]; mapping={}; cases={}; hashes={}
    for row in seed_rows:
        eid=row['id']; caseid='case-'+eid; sample='sample-'+eid
        observation={f.name:'FAKE-UNIT-TEST' for f in fields(ExperimentalObservation) if f.default is MISSING and f.default_factory is MISSING}
        observation.update(observation_id=eid,experiment_id='FAKE-UNIT-TEST',run_id='fake-run',evaluation_case_id=caseid,
            attack_instance_id='fake-attack',attack_family='fake-family',provider='mock',target_model='FAKE-MODEL',
            condition='isolated_attack',status='completed',context_status='retained',generation_configuration={'temperature':0},
            requested_seed=7,effective_seed=7,provider_supports_seed=True,sequence_position=1,turn_index=1,
            ordered_messages=[{'role':'user','content':row['prompt']},{'role':'assistant','content':row['response']}],
            response=row['response'])
        path=observations/(eid+'.json'); digest=write(path,observation); hashes[str(path.relative_to(observations.parent))]=digest
        candidate={'evaluation_id':eid,'target_response':row['response'],'conversation_history':observation['ordered_messages'],
            'attack_family':'fake-family','legitimate_task':row['prompt'],'adversarial_objective':row['objective'],
            'source_artifact':str(path.resolve()),'source_sha256':digest}
        candidates.append(candidate)
        cases[caseid]={'legitimate_task':row['prompt'],'attacks':{'fake-attack':row['objective']}}
        items.append({key:candidate[key] for key in ['legitimate_task','adversarial_objective','target_response','conversation_history']}|{'sample_id':sample})
        # False deliberately exercises the real-source transport contract in a test-only package.
        # The fixture bundle, prompts, IDs, provider and package remain visibly fictional.
        mapping[sample]={key:candidate[key] for key in ['evaluation_id','source_artifact','source_sha256','attack_family']}|{'synthetic_fixture':False}
    write(observations.parent/'manifest.json',{'experiment_id':'FAKE-UNIT-TEST','successful_count':len(seed_rows),
        'failed_count':0,'dataset_identity':{'hash':sha},'artifact_hashes':hashes})
    write(phase4/'jbb_annotation_objectives_v1.json',{'version':'fake-v1','source_dataset_sha256':sha,'cases':cases})
    write(restricted/'candidates_v1.json',{'experiment_id':'FAKE-UNIT-TEST','objectives_version':'fake-v1','synthetic_fixture':True,'candidates':candidates})
    write(restricted/'blinded_batch_v1.json',{'schema_version':'human-annotation-v1','batch_id':'phase4-jbb-pilot-v1',
        'rubric_version':'FAKE-UNIT-TEST','synthetic_fixture':True,'items':items})
    write(restricted/'private_join_map_v1.json',{'schema_version':'human-annotation-map-v1','batch_id':'phase4-jbb-pilot-v1',
        'rubric_version':'FAKE-UNIT-TEST','synthetic_fixture':True,'mapping':mapping})
    write(observations.parent/'audit_summary.json',{'human_labels':0,'scientific_metrics':'insufficient_data','synthetic_fixture':True})
    package=root/'experiments/phase5/restricted_annotation_v2'
    prepare(phase4,package)
    return phase4
