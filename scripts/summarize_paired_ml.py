"""CPU-only reconstruction and paired CIs; never inference or original-run writes."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
import csv
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.metrics.objective_calibration import binary_metrics, choose_threshold, grouped_folds, percentile, validate_features, TOKENS
from core.prediction.baselines import LogisticRegressionBaseline, LogisticRegressionConfig

AGGREGATE = ROOT / 'data/calibration/objective_summary_recomputed.json'
METHOD = 'recomputed from stored features/labels, not stored predictions'


def load_rows(aggregate):
    source = (ROOT / aggregate['source_run']).resolve()
    retry = (ROOT / aggregate['source_retry']).resolve()
    source.relative_to(ROOT / 'experiments/local-runs/calibration')
    retry.relative_to(source)
    originals = {p.name: json.loads(p.read_text(encoding='utf-8')) for p in (source/'cases').glob('*.json')}
    updates = {p.name: json.loads(p.read_text(encoding='utf-8')) for p in (retry/'cases').glob('*.json')}
    assert all(name in originals and originals[name]['status']=='failed' and originals[name].get('finish_reason')=='length' for name in updates)
    rows = []
    for value in {**originals, **updates}.values():
        if value['task'] != 'canary' or value['status'] != 'completed': continue
        if type(value.get('label')) is not int or value['label'] not in (0,1): continue
        validate_features(value['features'])
        rows.append({k:value[k] for k in ('id','model','template_id','features','label')})
    return rows


def reconstruct(rows, group_key):
    outputs = []
    config = LogisticRegressionConfig(300, .1, .01)
    for group, train_ids, test_ids in grouped_folds(rows, group_key):
        train, test = [rows[i] for i in train_ids], [rows[i] for i in test_ids]
        labels = [r['label'] for r in train]
        if len(set(labels)) < 2: raise ValueError('Cannot reproduce: one-class training fold')
        templates = sorted({r['features']['template_id'] for r in train})
        types = sorted({r['features']['prompt_type'] for r in train})
        lengths = [r['features']['prompt_length'] for r in train]
        mean = sum(lengths)/len(lengths)
        scale = math.sqrt(sum((v-mean)**2 for v in lengths)/len(lengths)) or 1
        def vector(row):
            f=row['features']
            return [(f['prompt_length']-mean)/scale]+[float(f['template_id']==v) for v in templates]+[float(f['prompt_type']==v) for v in types]+[float(f['style_tokens'][v]) for v in TOKENS]
        model = LogisticRegressionBaseline.fit([vector(r) for r in train], labels, config)
        train_scores = [p.raw_score for p in model.predict([vector(r) for r in train])]
        threshold = choose_threshold(labels, train_scores)
        prevalence = sum(labels)/len(labels)
        scores = [p.raw_score for p in model.predict([vector(r) for r in test])]
        for row, score in zip(test, scores):
            outputs.append({'id':row['id'],'model':row['model'],'template_id':row['template_id'],'label':row['label'],
                'score':score,'prediction':int(score>=threshold),'baseline_score':prevalence,'baseline_prediction':int(prevalence>.5),
                'outer_group':group,'threshold_train_only':threshold})
    return outputs


def ap(rows, baseline=False):
    return binary_metrics([r['label'] for r in rows], [r['baseline_score' if baseline else 'score'] for r in rows], [r['baseline_prediction' if baseline else 'prediction'] for r in rows])['pr_auc']


def paired_interval(rows, group_key, seed=42, resamples=1000):
    clusters=defaultdict(list)
    for row in rows: clusters[row[group_key]].append(row)
    if len(clusters)<2:
        return {'ci95':None,'includes_zero':None,'reason':'Fewer than two resampling groups','group_count':len(clusters)}
    rng=random.Random(seed); differences=[]
    for _ in range(resamples):
        sampled=[r for group in rng.choices(sorted(clusters),k=len(clusters)) for r in clusters[group]]
        left,right=ap(sampled),ap(sampled,True)
        if left is not None and right is not None: differences.append(left-right)
    ci=[percentile(differences,.025),percentile(differences,.975)] if differences else None
    return {'ci95':ci,'includes_zero':ci[0]<=0<=ci[1] if ci else None,'undefined_resamples':resamples-len(differences),
            'group_count':len(clusters),'bootstrap_unit':group_key,'resamples':resamples,'seed':seed,
            'limitation':'Fixed OOF predictions; not retraining uncertainty. Three model groups give particularly fragile intervals.'}


def wilson(successes, n):
    if not n: return None
    z=1.959963984540054; p=successes/n; denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return [max(0,center-radius),min(1,center+radius)]


def self_check():
    equal=[{'label':label,'score':.5,'baseline_score':.5,'prediction':0,'baseline_prediction':0,'template_id':group} for group in ('a','b') for label in (0,1)]
    result=paired_interval(equal,'template_id',resamples=50)
    assert result['ci95']==[0,0] and result['includes_zero'] is True
    perfect=[{**r,'score':float(r['label']),'prediction':r['label']} for r in equal]
    result=paired_interval(perfect,'template_id',resamples=50)
    assert result['ci95']==[.5,.5] and result['includes_zero'] is False
    assert wilson(0,0) is None
    print('SELF_CHECK_PASS',3)


def execute(scores_out=None, scores_in=None):
    if scores_out is not None and scores_out.exists(): raise FileExistsError('New reconstructed score file already exists')
    aggregate=json.loads(AGGREGATE.read_text(encoding='utf-8'))
    previous_prediction=json.dumps(aggregate['prediction'],sort_keys=True)
    if scores_in:
        predictions=json.loads(scores_in.read_text(encoding='utf-8'))['predictions']
    else:
        rows=load_rows(aggregate)
        predictions={key:reconstruct(rows,key) for key in ('template_id','model')}
    checks={}
    for key, output in predictions.items():
        checks[key]={}
        for name, baseline in (('logistic',False),('majority',True)):
            reproduced=ap(output,baseline); stored=aggregate['prediction'][key][name]['pr_auc']
            if reproduced is None or stored is None or abs(reproduced-stored)>.005:
                raise ValueError('Reproduction failed: '+key+' '+name+' AP not within 0.005; do not use the refit')
            checks[key][name]={'stored_ap':stored,'reproduced_ap':reproduced,'difference':reproduced-stored,'tolerance':.005}
    if scores_in is None:
        scores_out.parent.mkdir(parents=True,exist_ok=True)
        with scores_out.open('x',encoding='utf-8') as f: json.dump({'method':METHOD,'script':'scripts/summarize_paired_ml.py','predictions':predictions},f,ensure_ascii=True)
    score_file=scores_in if scores_in else scores_out
    # Use the persisted NEW scores, not transient fit state, for paired resampling.
    stored=json.loads(score_file.read_text(encoding='utf-8'))['predictions']
    result={'method':METHOD,'script':'scripts/summarize_paired_ml.py','score_file_sha256':hashlib.sha256(score_file.read_bytes()).hexdigest(),
            'reproduction_checks':checks,'settings':{'seed':42,'resamples':1000,'max_iterations':300,'learning_rate':.1,'l2_regularization':.01},
            'estimator':'deterministic L2 logistic regression; this is the sole stored model, so model-vs-majority and logistic-vs-majority are the same comparison',
            'comparisons':{}}
    for key, output in stored.items():
        left,right=ap(output),ap(output,True)
        result['comparisons'][key]={'logistic_ap':left,'majority_ap':right,'ap_difference':left-right,**paired_interval(output,key),
            'method':METHOD,'script':'scripts/summarize_paired_ml.py',
            'legacy_stored_ci_reference':'prediction.'+key+'.bootstrap.difference.pr_auc',
            'legacy_stored_ci_unit':aggregate['prediction'][key]['bootstrap_unit']}
        print('PAIRED_AP',key,json.dumps(result['comparisons'][key],ensure_ascii=True))
    judge_path=ROOT/'experiments/local-runs/canary-devtest/devtest-20261018-042016/test_metrics.json'
    judge=json.loads(judge_path.read_text(encoding='utf-8'))
    judge_intervals={}
    for variant in ('V0','V3'):
        r=judge[variant]; negative=r['n']-r['unsafe']
        judge_intervals[variant]={'n':r['n'],'non_safe':r['unsafe'],'tp':r['tp'],'fp':r['fp'],
            'recall':r['recall'],'recall_ci95':r['recall_ci95'],'fpr':r['fpr'],'fpr_wilson_ci95':wilson(r['fp'],negative),
            'source':'experiments/local-runs/canary-devtest/devtest-20261018-042016/test_metrics.json'}
    result['judge_reference_intervals']=judge_intervals
    human_root=ROOT/'experiments/local-runs/controlled/verification-20261017-232316/labeling/human_kit'
    def csv_rows(path):
        with path.open(encoding='utf-8') as f: return list(csv.DictReader(line.lstrip('\ufeff') if i==0 else line for i,line in enumerate(f)))
    humans=csv_rows(human_root/'human_sheet.csv'); key=csv_rows(human_root/'human_key.csv')
    by_id={r['id']:r for r in key}
    assert len(by_id)==len(key) and len({r['id'] for r in humans})==len(humans)
    allowed={'safe','unsafe','borderline'}
    pairs=[(r['label'],by_id[r['id']]['llm_reference']) for r in humans if r['id'] in by_id and r.get('label') in allowed and by_id[r['id']].get('llm_reference') in allowed]
    matches=sum(a==b for a,b in pairs); n=len(pairs)
    result['human_llm_reference_agreement_interval']={'matches':matches,'n':n,'wilson_ci95':wilson(matches,n),'excluded_rows':len(humans)-n,
        'sources':['experiments/local-runs/controlled/verification-20261017-232316/labeling/human_kit/'+p for p in ('human_sheet.csv','human_key.csv')],
        'scope':'Conditional selected single-labeler check, not population accuracy'}
    aggregate['paired_ml_differences']=result
    assert json.dumps(aggregate['prediction'],sort_keys=True)==previous_prediction
    temporary=AGGREGATE.with_name(AGGREGATE.name+'.pending')
    with temporary.open('w',encoding='utf-8') as f: json.dump(aggregate,f,indent=2,ensure_ascii=True)
    temporary.replace(AGGREGATE)
    print('REPRODUCTION_PASS',len(checks)*2,'NEW_SCORE_ROWS',sum(len(v) for v in predictions.values()))
    print('REPORT_INTERVALS',json.dumps({'judge':judge_intervals,'human_llm':result['human_llm_reference_agreement_interval']},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scores-out',type=Path,help='NEW local score file, outside old run folders')
    parser.add_argument('--scores-in',type=Path,help='Previously recreated local OOF scores; no refit')
    parser.add_argument('--self-check',action='store_true')
    args=parser.parse_args()
    if args.self_check: self_check()
    elif args.scores_in and not args.scores_out: execute(scores_in=args.scores_in)
    elif args.scores_out and not args.scores_in: execute(scores_out=args.scores_out)
    else: parser.error('Exactly one of --scores-out, --scores-in or --self-check is required')
