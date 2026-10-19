"""Synthetic, dependency-free objective scoring and grouped evaluation checks."""
import pytest
from core.metrics.objective_calibration import (score_answer, proxy_lift, prompt_features, validate_features, grouped_folds, evaluate_prediction)
from scripts.run_objective_calibration import prompt_set, gate
from core.metrics.objective_calibration import binary_metrics


@pytest.mark.parametrize('text,expected', [('ANSWER: ZX 12-34','correct'), ('ANSWER: other','hallucinated'), ('ABSTAIN','abstain'), ('I do not know.','abstain'), ('ANSWER: unknown','abstain'), ('A sentence about unknown things','failed'), ('ANSWER: x\nANSWER: y','failed')])
def test_fixed_extractor_and_abstain(text, expected):
    assert score_answer(text, 'zx1234')['outcome'] == expected


def test_failed_generation_never_scores_correct_or_safe():
    assert score_answer('ANSWER: x', 'x', completed=False)['outcome'] == 'failed'
    assert score_answer('ANSWER: x', 'x', retained=False)['outcome'] == 'failed'


def test_pr_auc_constant_score_ties_are_order_independent():
    for labels in ([1,1,0,0], [0,0,1,1], [1,0,1,0]):
        assert binary_metrics(labels, [.5]*4, [0]*4)['pr_auc']==.5


def test_context_proxy_preserves_denominators_and_pair_bootstrap():
    rows=[{'pair_id':'a','arm':'grounded','outcome':'correct'}, {'pair_id':'a','arm':'ungrounded','outcome':'hallucinated'},
          {'pair_id':'b','arm':'grounded','outcome':'correct'}, {'pair_id':'b','arm':'ungrounded','outcome':'abstain'},
          {'pair_id':'c','arm':'grounded','outcome':'failed'}, {'pair_id':'c','arm':'ungrounded','outcome':'hallucinated'}]
    result=proxy_lift(rows,50)
    assert result['lift']==.5 and result['complete_pairs']==2 and result['incomplete_pairs']==1
    assert result['ci95']==[0,1]
    assert result['counts']['grounded']['failed']==1
    assert 'NOT canonical' in result['scope']
    empty=proxy_lift([{'pair_id':'x','arm':'grounded','outcome':'failed'}])
    assert empty['lift'] is None and empty['ci95'] is None


def test_prompt_whitelist_rejects_response_or_marker_features():
    f=prompt_features('synthetic-a','injection','ignore and join placeholders')
    validate_features(f)
    for name in ('output','marker','oracle_label','latency_ms'):
        with pytest.raises(ValueError): validate_features({**f,name:'synthetic-excluded'})


def test_leave_group_out_has_no_template_or_model_overlap():
    rows=[{'template_id':f't{i}','model':f'm{j}'} for i in range(3) for j in range(3)]
    for key in ('template_id','model'):
        tests=[]
        for _,train,test in grouped_folds(rows,key):
            assert {rows[i][key] for i in train}.isdisjoint({rows[i][key] for i in test})
            tests+=test
        assert sorted(tests)==list(range(9))


def test_prediction_reports_baselines_intervals_and_train_only_thresholds():
    rows=[{'template_id':f't{i}','model':f'm{j}','features':prompt_features(f't{i}','injection' if y else 'benign','ignore secret' if y else 'primary color'), 'label':y}
          for i in range(3) for j in range(2) for y in (0,1)]
    result=evaluate_prediction(rows,'template_id',resamples=20)
    assert result['logistic']['n']==12
    assert result['logistic']['pr_auc'] is not None and result['majority']['pr_auc'] is not None
    assert result['bootstrap']['logistic']['pr_auc']['ci95'] is not None
    assert all('threshold_train_only' in f for f in result['folds'])
    assert result['resamples']==20


def test_prompt_set_is_frozen_and_generation_gate_excludes_failures():
    a,b=prompt_set(),prompt_set()
    assert a==b and len(a)==240
    assert sum(c['task']=='qa' for c in a)==120
    assert len({c['template_id'] for c in a if c['task']=='canary'})==12
    rows=[{'task':'canary','status':'completed','label':y,'template_id':f't{i}'} for i in range(5) for y in (0,1) for _ in range(6)]
    assert gate(rows)['met']
    rows.append({'task':'canary','status':'failed','label':None,'template_id':'t0'})
    assert gate(rows)['positives']==30 and gate(rows)['failed']==1


def test_objective_data_missing_stays_unavailable_without_replacing_canonical_metric(tmp_path):
    from apps.api.metric_calibration import build_calibration
    for metric in ('mchl','ml'):
        output=build_calibration(metric,[],[],0,tmp_path)
        assert output['objective_evidence'] is None
        assert output['status']=='not_established'
        assert any('objective aggregate' in text for text in output['missing_evidence'])


def test_objective_aggregate_is_separate_and_never_upgrades_scientific_claim(tmp_path):
    import json
    from apps.api.metric_calibration import build_calibration,OBJECTIVE_SUMMARY
    path=tmp_path/OBJECTIVE_SUMMARY; path.parent.mkdir(parents=True)
    data={'schema_version':'objective-calibration-v1','scope':'SYNTHETIC TEST ONLY','source_run':'synthetic-run',
          'gate':{'met':True,'positives':31,'mixed_template_groups':5},'feature_names':['template_id'],'limitations':['Synthetic only'],
          'hallucination_proxy':{'synthetic-model':{'complete_pairs':0,'lift':None,'ci95':None}},
          'prediction':{group:{'folds':[{'status':'computed'},{'status':'computed'}]} for group in ('template_id','model')}}
    path.write_text(json.dumps(data),encoding='utf-8')
    qa=build_calibration('mchl',[],[],0,tmp_path)
    ml=build_calibration('ml',[],[],0,tmp_path)
    assert qa['objective_evidence']['hallucination_proxy']['synthetic-model']['lift'] is None
    assert qa['criteria'][-1]['met'] is False
    assert ml['criteria'][-1]['met'] is True
    assert qa['status']==ml['status']=='not_established'
    assert not any('risk_score' in str(c) for c in ml['criteria'])
