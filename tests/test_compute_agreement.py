import pytest
from scripts.compute_agreement import agreement


def test_synthetic_three_class_kappa_and_degenerate_case():
    left = ['safe', 'safe', 'unsafe', 'unsafe', 'borderline', 'borderline']
    right = ['safe', 'unsafe', 'unsafe', 'unsafe', 'borderline', 'safe']
    result = agreement(left, right)
    assert result['n'] == 6
    assert result['kappa'] == pytest.approx(0.5)
    assert result['agreement_percent'] == pytest.approx(100 * 4 / 6)
    assert result['confusion_matrix']['safe']['unsafe'] == 1
    assert sum(sum(row.values()) for row in result['confusion_matrix'].values()) == 6
    assert agreement(left, left)['kappa'] == 1
    assert agreement(['safe'], ['safe'])['kappa'] is None
    assert agreement(['safe'], ['unsafe'])['kappa'] == 0
    with pytest.raises(ValueError, match='Unsupported'):
        agreement(['missing'], ['safe'])


def test_extended_metrics_with_synthetic_three_class_data():
    from scripts.compute_agreement import extended_metrics
    reference=['safe','safe','unsafe','borderline']
    predicted=['safe','unsafe','unsafe','borderline']
    result=extended_metrics(reference,predicted)
    assert result['agreement_percent']==75
    assert result['ac1']==pytest.approx(27/43)
    assert result['pabak']==pytest.approx(.625)
    assert result['pabak_binary_non_safe']==.5
    assert result['per_class']['unsafe']['precision']==.5
    assert result['per_class']['unsafe']['recall']==1
    assert result['non_safe']['precision']==pytest.approx(2/3)
    assert result['bootstrap']['resamples']==1000
    assert result['bootstrap']['seed']==42
    assert result['bootstrap']==extended_metrics(reference,predicted)['bootstrap']
    constant=extended_metrics(['safe'],['safe'])
    assert constant['per_class']['unsafe']['precision'] is None
    assert constant['non_safe']['recall'] is None
    assert constant['bootstrap']['ac1_ci95']==[1,1]


def test_wilson_and_variant_abstention_with_synthetic_labels():
    from scripts.compute_agreement import wilson_ci, variant_metrics
    assert wilson_ci(1,4) == pytest.approx([.0455872608,.6993581574])
    assert wilson_ci(0,0) is None
    assert wilson_ci(0,2)[0] == 0
    with pytest.raises(ValueError):
        wilson_ci(3,2)
    result=variant_metrics(['safe','unsafe','borderline','unsafe'],
        ['unsafe','invalid','borderline','unsafe'],[True,True,False,True],[1,2,3,4])
    assert result['recall']==.5
    assert result['recall_support']==2
    assert result['precision']==pytest.approx(2/3)
    assert result['f1']==pytest.approx(4/7)
    assert result['invalid']==1
    assert result['raw_percent']==50
    assert result['ac1_valid_pairs']==3
    assert result['avg_latency_ms']==2.5
    invalid=variant_metrics(['unsafe'],['invalid'])
    assert invalid['recall']==0 and invalid['precision'] is None
    assert invalid['ac1'] is None and invalid['raw_percent']==0
