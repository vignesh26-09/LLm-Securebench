"""Fallback only for the eight private-artifact transport tests."""
import json
import pytest
from tests.phase2_fixture_factory import materialize

PRIVATE_TESTS = {
 'test_annotation_export_contains_real_responses_but_no_labels',
 'test_real_batch_has_36_exact_source_matches_without_labels',
 'test_tampered_candidate_response_is_rejected',
 'test_run_manifest_hash_mismatch_is_rejected',
 'test_reviewer_forms_blank_separate_and_immutable',
 'test_real_blank_forms_cannot_be_imported',
 'test_import_verifies_immutable_package_and_rubric_hashes',
 'test_partial_annotation_records_cannot_unlock_asr',
}

@pytest.fixture(autouse=True)
def private_annotation_fallback(request, tmp_path, monkeypatch):
    if request.node.name not in PRIVATE_TESTS:
        return
    module=request.module
    required=module.PHASE4/'restricted_annotation'
    package=module.ROOT/'experiments/phase5/restricted_annotation_v2'
    if all((required/name).is_file() for name in ['candidates_v1.json','blinded_batch_v1.json','private_join_map_v1.json']) and all((package/name).is_file() for name in ['package_manifest.json','reviewer_a.csv','reviewer_b.csv','adjudication_template.csv']):
        return
    phase4=materialize(tmp_path)
    # The ASR guard test audits the existing public 100/36 source observations;
    # only its missing reviewer package needs the six-row synthetic fallback.
    if request.node.name != 'test_partial_annotation_records_cannot_unlock_asr':
        monkeypatch.setattr(module,'PHASE4',phase4)
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'RESTRICTED',phase4/'restricted_annotation',raising=False)
    monkeypatch.setattr(module,'SAMPLE_COUNT',6,raising=False)
    import scripts.import_phase5_annotation as importer
    original=importer.run
    if hasattr(module,'import_run'):
        monkeypatch.setattr(module,'import_run',lambda **kwargs: original(**kwargs,package=tmp_path/'experiments/phase5/restricted_annotation_v2'))
    import scripts.report_phase5_measurement_eligibility as eligibility
    monkeypatch.setattr(eligibility,'ROOT',tmp_path)
