# Explicitly synthetic annotation fixtures
Six fictional harmless rows; no private data, labels or research observations.
The factory materializes the existing observation/candidate/blinded/map schemas,
hashes and blank reviewer packages in pytest temporary directories.
The map entry synthetic_fixture=false is a deliberate test input for the
real-source-only audit contract; the enclosing bundles are marked synthetic,
with FAKE identifiers, mock provider and fake text. Never import as evidence.
Production audit checks are unchanged. Real files take precedence when present.

Eight fallback tests: test_annotation_export_contains_real_responses_but_no_labels;
test_real_batch_has_36_exact_source_matches_without_labels;
test_tampered_candidate_response_is_rejected; test_run_manifest_hash_mismatch_is_rejected;
test_reviewer_forms_blank_separate_and_immutable; test_real_blank_forms_cannot_be_imported;
test_import_verifies_immutable_package_and_rubric_hashes;
test_partial_annotation_records_cannot_unlock_asr.

Required original files: experiments/phase4/restricted_annotation/{candidates_v1.json,
blinded_batch_v1.json,private_join_map_v1.json}; experiments/phase5/restricted_annotation_v2/
{package_manifest.json,reviewer_a.csv,reviewer_b.csv,adjudication_template.csv}, plus
the package source audit and pinned rubrics. Source observations, objectives,
dataset, specification, lock and manifest must remain hash-aligned.
