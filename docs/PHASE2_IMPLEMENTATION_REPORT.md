# Phase 2 implementation and verification report

**Date:** 10 October 2026. This is an incremental backend implementation, not completion of the empirical study.

## Implemented in this pass

- Audited existing demonstration, controlled-run, metric, persistence, reporting, and evaluator paths in `PHASE2_REPOSITORY_AUDIT.md`.
- Added `core/evaluation/annotation_candidates.py` and `scripts/build_annotation_candidates.py`: extract only completed attack observations, require separately declared task/objective text, preserve conversation history and response, bind each row to an immutable source file and SHA-256.
- Added `core/evaluation/annotation_workflow.py` and `scripts/annotation_batch.py`: randomized blinded export with a separate private join map; two independent labels; explicit conflict adjudication; rejection of unsolicited adjudication, duplicate/unknown labels, missing objectives, and changed source artifacts; append-only individual, adjudication, and derived outcome records. Synthetic examples are explicitly marked fixtures.
- Added `core/evaluation/automated_outcome.py`: strict outcome-specific structured parser and provider adapter. Automated confidence is uncalibrated; provider/parse failure produces unavailable, never a fabricated human label.
- Added `core/evaluation/split_integrity.py`: disjoint declared related-prompt groups across development, validation, and test. This is a structural leakage check, not semantic near-duplicate detection.
- Extended new judge calibration artifacts with specificity and balanced accuracy without changing the historical JailbreakBench record or its predeclared label mapping. Added `scripts/verify_persisted_judge_calibration.py` for read-only, offline source-hash and confusion-matrix verification.
- Added the requested research, metric, evaluation, protocol, statistical-plan, reproducibility, threat-model, and paper-readiness documents. No BSDA/RC/SAEA formula was changed.

## Verified evidence and tests

Baseline before edits: 167 passed. Final: **182 passed, one upstream Starlette/httpx deprecation warning** using `F:\SecureLLM\.venv\Scripts\python.exe -m pytest -q` with `TEMP` and `TMP` set to `F:\SecureLLM.tmp`. `scripts/api_smoke.py` and `scripts/end_to_end_smoke.py` passed. The API smoke checked health, readiness, review creation, eight read resource routes, summary, and detail. End-to-end mock smoke persisted/reloaded three engineering evaluations.

Offline verification from persisted `experiments/jailbreakbench-validation/results.json` and source manifest: 300 source, 295 usable, coverage 0.9833333333, raw agreement 0.5389830508, Cohen's κ 0.2112609602; confusion counts TN=51, FN=1, FP=135, TP=108. Source SHA-256 matches its manifest. This weak judge agreement precludes substituting the current judge for independent human outcome labels. A legacy script named `validate_jailbreakbench_judge.py` actually makes live judge calls and was stopped after detecting this; it did not rewrite the stored artifact. Use the offline paper-evidence recomputation for verification.

Current SQLite counts: 13 benchmark runs, 39 evaluations, 117 Layer 1 records, zero Layer 2 records, 89 scientific records. These counts are local database state, not a Phase 1 scientific sample. The only eligible paper chart remains real judge calibration; BSDA/RC/SAEA charts lack qualifying records.

## Exact reproduction commands

In PowerShell from `F:\SecureLLM`:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
F:\SecureLLM\.venv\Scripts\python.exe -m pytest -q
F:\SecureLLM\.venv\Scripts\python.exe scripts\api_smoke.py
F:\SecureLLM\.venv\Scripts\python.exe scripts\end_to_end_smoke.py
F:\SecureLLM\.venv\Scripts\python.exe scripts\verify_persisted_judge_calibration.py
```

For a real completed controlled run, first create a reviewed case-objectives JSON, then use:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe scripts\build_annotation_candidates.py --observations RUN_DIR\observations --objectives OBJECTIVES.json --experiment-id EXPERIMENT_ID --output CANDIDATES.json
F:\SecureLLM\.venv\Scripts\python.exe scripts\annotation_batch.py export --candidates CANDIDATES.json --public RATER_BATCH.json --private-map PRIVATE_MAP.json --batch-id BATCH_ID --rubric-version v1
F:\SecureLLM\.venv\Scripts\python.exe scripts\annotation_batch.py import --public RATER_BATCH.json --private-map PRIVATE_MAP.json --judgments HUMAN_JUDGMENTS.json --adjudications HUMAN_ADJUDICATIONS.json --label-version v1 --database securellmbench.db
```

The second command requires actual independent human judgments; examples and test fixtures do not qualify.

## Remaining scientific blockers

The controlled CLI still does not independently verify dataset source bytes or require a locked preregistration, and it lacks a matched benign conversation condition. No validated behavioral-state measurement bridge or Phase 1 BSDA/RC/SAEA dataset exists. Automated outcome reliability has not been established on held-out independent human labels, and no grouped multi-model statistical inference has been executed. The project is ready for further controlled data collection and evaluator validation, but the proposed empirical conference paper is not yet supported by findings.
