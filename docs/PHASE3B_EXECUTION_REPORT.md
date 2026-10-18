# Phase 3B implementation and execution report

## Verified change

The controlled experiment runner now has a matched benign three-turn lane and benign post-conversation probes in addition to existing fresh baselines, isolated attacks, two ordered sequences, and attacked recovery probes. It preserves deterministic append-only observations, full ordered histories, canary/context evidence, matched control identities, and contamination records. Existing BSDA, recovery, and SAEA formulas were not changed.

The controlled CLI now verifies the actual source dataset SHA-256 and case content, a locally frozen protocol/specification hash, exact installed Ollama model digests, and a positive `--max-calls` cap **before** inference. `--dry-run` reports the cap without target calls. Pilot execution requires an explicit separate database and carries `engineering_pilot` plus synthetic provenance, excluded by paper-chart eligibility. Fresh SQLite schema creation was added after the first real pilot exposed a missing-table defect; immutable saved observations were resumed rather than rerun. Empty Ollama conversation text now becomes a failed observation instead of crashing during assistant-message construction.

Added `core/experiments/dataset_audit.py` for future source manifests: provenance/license/revision/checksum, case IDs and objectives, declared split/group isolation, exact duplicate rejection, and lexical near-duplicate review flags. It cannot prove semantic non-leakage or dataset scientific fitness. `scripts/report_phase3b_pilot.py` verifies saved file hashes, database record count/class, and evidence counts; it deliberately computes no scientific score.

## Exact reproducibility commands (PowerShell from `F:\SecureLLM`)

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\prepare_phase3b_pilot.py
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\run_controlled_experiment.py experiments\phase3b\pilot_specification_v1.json --dataset-source experiments\phase3b\pilot_dataset_v1.json --protocol-lock experiments\phase3b\pilot_protocol_lock_v1.json --max-calls 50 --output experiments\phase3b\pilot_run_v1 --database experiments\phase3b\pilot_v1.db --evidence-class engineering_pilot --dry-run
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\run_controlled_experiment.py experiments\phase3b\pilot_specification_v1.json --dataset-source experiments\phase3b\pilot_dataset_v1.json --protocol-lock experiments\phase3b\pilot_protocol_lock_v1.json --max-calls 50 --output experiments\phase3b\pilot_run_v1 --database experiments\phase3b\pilot_v1.db --evidence-class engineering_pilot
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\report_phase3b_pilot.py --run-dir experiments\phase3b\pilot_run_v1 --database experiments\phase3b\pilot_v1.db --output experiments\phase3b\pilot_run_v1\audit_summary.json
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\verify_persisted_judge_calibration.py
& 'F:\SecureLLM\.venv\Scripts\python.exe' -m pytest -q
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\api_smoke.py
```

The actual pilot completed 50/50 local calls and persisted 50/50 observations, 25/model, with zero provider failures. The output manifest SHA-256 is `86b54a35ba2ecf6281dc62dc2769b510a92dce7547f6e17dd854bc839cb210da`. Re-running the same command resumes; it should not reissue the saved target calls. A new pilot design requires a new version/experiment ID and lock, rather than `--force` overwriting evidence. The observation timestamp span is about 18 seconds; this is not a complete runtime benchmark. The pilot's call cap and 90-second per-call timeout bound call count and individual requests, not every possible process-level failure mode.

## Validation results

- Baseline before changes: **190 passed, 1 third-party deprecation warning**.
- After changes: **196 passed, 1 third-party deprecation warning** (`pytest -q`). New tests cover full benign/attacked condition counts and histories, resume without repeated calls, source/lock mutation rejection, cross-split leakage/near-duplicate review, fresh pilot database initialization/provenance, and empty Ollama text with `done_reason=length`.
- Persisted JailbreakBench calibration verification: 300 source, 295 usable, TN=51, FP=135, FN=1, TP=108, coverage 98.33%, agreement 53.90%, κ=0.2112609601698581; source SHA-256 `dacaf76a1057785f11b0fc6aa07b9a73cdab588319ddfc5e8cef2909e5b112a5`.
- API smoke on in-memory database: `/health` 200, `/ready` 200, review creation 201, eight read resources plus summary/detail checks passed. Scientific claims validated flag remained false.
- Actual pilot-database API readback: `/health` and `/ready` 200; `/scientific-records` 200 with a 50-item first page whose provenance says `engineering_pilot`; `/reports/charts/bsda_distribution` returned `insufficient_data`.
- Actual pilot-database chart check: BSDA, recovery, SAEA, and applicability summary each returned `insufficient_data`; no pilot plot was exported.

Frontend checks were outside this backend-only Phase 3B pass. No remote paid service or model download was used. The historical calibration and unrelated local changes were preserved.
