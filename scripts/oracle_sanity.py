"""No inference: apply oracle/hybrid to read-only cached canary outputs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core.judging.oracle_checks import check, hybrid_policy

SOURCE=ROOT/'experiments/local-runs/canary/canary-20261018-035526'
PROTECTED=(SOURCE,ROOT/'experiments/local-runs/canary-devtest/devtest-20261018-042016',
    ROOT/'experiments/local-runs/controlled/verification-20261017-232316/labeling')
MODELS=('gemma3:4b','qwen3.5:2b','llama3.2:3b')
NOTE='by construction: canary ground truth is the same rule; NOT an accuracy result'


def execute(folder):
    if folder.exists():
        if {p.name for p in folder.iterdir()}!={'protected_hashes.json'}:
            raise ValueError('Only an unfinished hash-only sanity folder can be resumed')
    else:
        folder.mkdir(parents=True,exist_ok=False)
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for root in PROTECTED for p in root.iterdir() if p.is_file()}
    snapshot=folder/'protected_hashes.json'
    if snapshot.exists():
        if json.loads(snapshot.read_text(encoding='utf8'))!=hashes:raise RuntimeError('Protected inputs changed since first attempt')
    else:
        snapshot.write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf8')
    prompts={r['id']:r for r in [json.loads(x) for x in (SOURCE/'prompts_canary_v1.jsonl').read_text(encoding='utf8').splitlines()]}
    cached={r['id']:r for r in [json.loads(x) for x in (SOURCE/'judge_V0.jsonl').read_text(encoding='utf8').splitlines()]}
    fired=0;v0=Counter();hybrid=Counter();total=0
    for model in MODELS:
        path=SOURCE/('generation_'+model.split(':')[0]+'.jsonl')
        for line in path.read_text(encoding='utf8').splitlines():
            row=json.loads(line);prompt=prompts[row['id']]
            if row['status']!='completed' or not row['output'].strip():raise ValueError('Missing cached output; never regenerate or count safe')
            token=prompt['rule']['regex']
            if not token.isalnum():raise ValueError('Fixture token must be literal alphanumeric text, not an arbitrary regex')
            secrets=[token] if prompt['category']=='secret_leak' else []
            markers=[] if secrets else [token]
            verdict=cached[model+'::'+row['id']]['label']
            result=check(row['output'],secrets,markers)
            combined=hybrid_policy(row['output'],secrets,markers,verdict_mode='hybrid',judge=lambda:{'label':verdict})
            fired+=result['fired'];v0[verdict]+=1;hybrid[combined['label']]+=1;total+=1
    if total!=180:raise ValueError('Expected 180 cached outputs')
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=value for p,value in hashes.items()):raise RuntimeError('Protected input changed')
    summary={'label':NOTE,'outputs':total,'oracle_fired':fired,'verdict_counts':{'V0':dict(v0),'hybrid':dict(hybrid)},'llm_calls':0,
        'caveat':'Known-token matching underlies both fixture and oracle. Expanded normalization/encoding/8-character fragments are broader than the original exact regex. These counts are not an accuracy estimate.',
        'evidence':'Cached V0 verdicts only; no model calls, no generation, no changes to source run/labeling files. No matched values are saved.'}
    (folder/'sanity_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    lines=['# '+NOTE,'',f'Oracle fired: {fired}/{total}.','', '| Policy | Verdict counts |','|---|---|',
        '| V0 | '+json.dumps(dict(v0))+' |','| Hybrid | '+json.dumps(dict(hybrid))+' |','',summary['caveat'],summary['evidence']]
    (folder/'sanity_report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(NOTE)
    print(f'Oracle fired: {fired}/{total}; V0 {dict(v0)}; hybrid {dict(hybrid)}')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    execute(parser.parse_args().output)
