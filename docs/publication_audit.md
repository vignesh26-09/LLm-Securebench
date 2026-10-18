## Public snapshot status (public-clean)

| Check | Count/status |
|---|---|
| Tracked files in published baseline | 589 |
| Tracked blocker paths / archives / databases / files >10 MiB | 0 / 0 / 0 / 0 |
| Secret shape scan, user-verified context; not rerun | 0 matches |
| Reviewed benign lines, excluded from this scan; locations omitted | 8 |
| Documentation path replacements | 151 across 33 files |
| Code/data/other files with retained absolute paths | 11 files / 17 occurrences |
| Name-like field keys | 35 files / 160 occurrences |
| Requested personal/identity/name-term candidates | 0 files / 0 occurrences |
| Ignore patterns added | 0 |

This tracked snapshot supersedes the older working-tree inventory below. Name-like schema keys are not evidence of personal data; identity/institution/acronym candidates require contextual review. No matched values or reviewed benign locations are reproduced.
Remaining dataset-licence review is required; upstream licences apply independently of the code licence. Counts describe the pre-edit tracked snapshot; no identity fields were edited. Extracted binary paper documents: 6; raster images without OCR: 8.

### Retained code/data paths (not edited)

| Path | Count | Use |
|---|---|---|
| artifacts/build_ieee_paper.py | 2 | functional default/path reference: 2 |
| core/feasibility_pilot/restricted_store.py | 1 | functional default/path reference: 1 |
| docs/paper/build_manuscript.ps1 | 2 | functional default/path reference: 2 |
| experiments/jailbreakbench-validation/pilot_results.json | 1 | recorded artifact text; runtime use not established: 1 |
| experiments/jailbreakbench-validation/results.json | 1 | recorded artifact text; runtime use not established: 1 |
| experiments/jailbreakbench-validation/smoke_results.json | 1 | recorded artifact text; runtime use not established: 1 |
| grafana/provisioning/dashboards/securellmbench.yml | 1 | functional configuration path: 1 |
| grafana/provisioning/datasources/securellmbench.yml | 1 | functional configuration path: 1 |
| scripts/build_paper_evidence.py | 5 | functional default/path reference: 5 |
| scripts/feasibility_mock_smoke.py | 1 | functional default/path reference: 1 |
| scripts/run_judge_variants.py | 1 | functional default/path reference: 1 |

### Name categories (values omitted)

| Path | Name-like field keys | Requested name-term candidates |
|---|---|---|
| apps/api/auth.py | 2 | 0 |
| apps/api/local_execution.py | 3 | 0 |
| artifacts/adapt_to_conference_template.py | 1 | 0 |
| artifacts/build_ieee_paper.py | 1 | 0 |
| core/dataset/benchmark_catalog.py | 2 | 0 |
| core/experiments/manifest.py | 1 | 0 |
| core/metrics/bsda.py | 1 | 0 |
| data/benchmark_10000.manifest.json | 1 | 0 |
| data/raw/example.json | 1 | 0 |
| docs/paper/securellmbench_references.bib | 11 | 0 |
| experiments/paper_2026/outputs/post_fix_local_trace.json | 42 | 0 |
| experiments/paper_2026/outputs/post_rubric_fix_local_trace.json | 42 | 0 |
| experiments/paper_2026/outputs/pre_fix_local_trace.json | 18 | 0 |
| experiments/paper_2026/run_experiment.py | 1 | 0 |
| experiments/phase3b/pilot_dataset_v1.json | 1 | 0 |
| experiments/phase3b/pilot_specification_v1.json | 3 | 0 |
| experiments/phase4/jbb_pilot_specification_v1.json | 2 | 0 |
| frontend/package-lock.json | 2 | 0 |
| frontend/package.json | 1 | 0 |
| scripts/build_10000_corpus.py | 1 | 0 |
| scripts/feasibility_provider_audit.py | 2 | 0 |
| scripts/prepare_phase3b_pilot.py | 2 | 0 |
| scripts/prepare_phase4_jbb_pilot.py | 2 | 0 |
| scripts/process_dataset.py | 1 | 0 |
| scripts/run_local_benchmark.py | 1 | 0 |
| tests/test_dataset.py | 1 | 0 |
| tests/test_feasibility_provider_audit.py | 2 | 0 |
| tests/test_full_corpus_execution.py | 3 | 0 |
| tests/test_large_benchmark_corpus.py | 1 | 0 |
| tests/test_local_execution.py | 1 | 0 |
| tests/test_model_connection.py | 1 | 0 |
| tests/test_ollama_judge_provider.py | 1 | 0 |
| tests/test_ollama_retries.py | 1 | 0 |
| tests/test_production_preflight.py | 3 | 0 |
| tests/test_workspace_auth.py | 1 | 0 |

## Working-tree audit, superseded for the published snapshot
# Publication audit

Read-only scan performed 2026-10-18. Excluded `.git`, `.tmp`, `node_modules`, `venv`, `.venv`, build output, and `*.log` from file-content scans. Findings below contain paths, counts, and categories only; matched values are omitted.

| Area | Status | Finding |
|---|---|---|
| Secrets, tokens, keys, passwords | WARN | 0 `.env` files; 0 high-confidence AWS/GitHub token patterns; 15 candidate credential assignments in 14 files require manual review. Candidate patterns can include test/config placeholders. |
| Personal data: email | OK | 17 email-shaped strings across 7 files; all detected domains are example/test/local placeholders. |
| Personal data: names | WARN | 40 name-like field patterns across 37 files; heuristic matches are not confirmed identities and require review before publication. |
| Personal data: phone | OK | No confirmed phone numbers; numeric patterns were not counted as personal data. |
| Personal data: local user paths | WARN | 5 `<PROJECT_ROOT> references across 4 files. |
| Absolute local paths | WARN | 236 Windows absolute path occurrences across 47 files (inventory below). |
| Large/binary artifacts | BLOCKER | `SecureLLM.zip` present (1 archive); publish only after manual contents review. |
| Large/binary artifacts | WARN | `securellmbench.db` present (1 database); 0 model weight files found. |
| Large files | WARN | 3 files exceed 10 MB: `securellmbench.db` (1), `data/external/anthropic_red_team_09be8c5.jsonl.gz` (1), `data/external/dolly_15k_bdd27f4.jsonl` (1). |
| Generated/raw runs | BLOCKER | `experiments/phase3b/pilot_run_v1/` (64 files), `experiments/phase4/jbb_pilot_run_v1/` (127 files), `experiments/local-runs/canary-devtest/` (16 files). |
| Excluded directories present | WARN | `.tmp/` (1), `.venv/` (1), `frontend/node_modules/` (1). These were excluded from content scanning. |
| `.gitignore` coverage | BLOCKER | The three raw run folders above lack matching ignore rules. |
| `.gitignore` coverage | WARN | Missing broad coverage for nested raw local-run output, generic `*.log`, nested `*.zip`, model weights, and generic `node_modules/`. Existing rules cover `.env*`, databases, root `SecureLLM.zip`, `.venv/`, and `venv/`. |
| Licence | OK | Root `LICENSE` present; both vendored JailbreakBench directories have a license file. |
| Dataset/third-party licence | WARN | 3 top-level external dataset assets have no adjacent license file in `data/external/`; verify their upstream terms before redistribution. |

## Absolute local path inventory

Counts are regex matches; paths are repository-relative.

| Path | Count |
|---|---:|
| `artifacts/adapt_to_conference_template.py` | 1 |
| `artifacts/build_ieee_paper.py` | 2 |
| `core/feasibility_pilot/restricted_store.py` | 1 |
| `data/external/jbb_artifacts_909e68c/PAIR-black_box-vicuna-13b-v1.5.json` | 1 |
| `docs/BACKEND_RESEARCH_AUDIT.md` | 1 |
| `docs/BENCHMARK_10000_CORPUS.md` | 7 |
| `docs/DASHBOARD_BACKEND_CONTINUATION.md` | 1 |
| `docs/DASHBOARD_PHASE12_IMPLEMENTATION.md` | 2 |
| `docs/GRAFANA_DASHBOARD.md` | 3 |
| `docs/HUMAN_ANNOTATION_PROTOCOL.md` | 3 |
| `docs/HUMAN_REVIEW_EXECUTION_CHECKLIST.md` | 3 |
| `docs/LOCAL_PIPELINE_AUDIT.md` | 4 |
| `docs/PAPER_FREEZE_REPORT.md` | 5 |
| `docs/PAPER_REPRODUCIBILITY.md` | 8 |
| `docs/PHASE2_IMPLEMENTATION_REPORT.md` | 12 |
| `docs/PHASE2_REPOSITORY_AUDIT.md` | 1 |
| `docs/PHASE3A_EVALUATOR_DIAGNOSTICS.md` | 2 |
| `docs/PHASE3B_EXECUTION_REPORT.md` | 10 |
| `docs/PHASE4_DATASET_INTEGRATION.md` | 2 |
| `docs/PHASE4_EMPIRICAL_EXECUTION.md` | 7 |
| `docs/PHASE5_RESEARCH_READINESS.md` | 9 |
| `docs/PHASE6_HUMAN_HANDOFF.md` | 3 |
| `docs/PHASE6_RESEARCH_READINESS.md` | 3 |
| `docs/PRI_IMPLEMENTATION_RECONCILIATION.md` | 1 |
| `docs/PRODUCTION_SCALE_PREFLIGHT.md` | 1 |
| `docs/PYTHON_ENVIRONMENT_REPAIR.md` | 9 |
| `docs/REPRODUCIBILITY_CHECKLIST.md` | 2 |
| `docs/REVIEWER_DISTRIBUTION_INSTRUCTIONS.md` | 1 |
| `docs/paper/SecureLLMBench_Paper_Evidence_Gaps.md` | 6 |
| `docs/paper/build_manuscript.ps1` | 3 |
| `docs/specs/feasibility_pilot/implementation_decisions.md` | 2 |
| `docs/specs/feasibility_pilot/novelty_ledger.md` | 7 |
| `docs/specs/feasibility_pilot/p6_1_mock_verification.md` | 4 |
| `docs/specs/feasibility_pilot/provider_audit.md` | 2 |
| `docs/specs/feasibility_pilot/tasks.md` | 4 |
| `experiments/jailbreakbench-validation/pilot_results.json` | 1 |
| `experiments/jailbreakbench-validation/results.json` | 1 |
| `experiments/jailbreakbench-validation/smoke_results.json` | 1 |
| `experiments/local-runs/canary-devtest/devtest-20261018-042016/source_hashes.json` | 19 |
| `experiments/local-runs/controlled/verification-20261017-232316/completion.json` | 2 |
| `experiments/local-runs/controlled/verification-20261017-232316/phase4_export_status.json` | 1 |
| `experiments/local-runs/controlled/verification-20261017-232316/state.json` | 2 |
| `experiments/local-runs/oracle-sanity/oracle-20261018-043342/protected_hashes.json` | 66 |
| `experiments/paper_2026/README.md` | 3 |
| `scripts/build_paper_evidence.py` | 5 |
| `scripts/feasibility_mock_smoke.py` | 1 |
| `scripts/run_judge_variants.py` | 1 |
