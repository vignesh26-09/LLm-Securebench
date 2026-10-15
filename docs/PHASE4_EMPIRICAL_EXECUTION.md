# Phase 4 real-source exploratory execution

**Observed execution:** `phase4-jbb-exploratory-pilot-v1` used pinned JailbreakBench source goals and official PAIR, GCG, and JBC attack strings for indices 1 and 51. The source was real; the study was small, unlabeled, and exploratory. The protocol was locally frozen before target calls, not externally preregistered. The target models were local `qwen3.5:2b` (digest `324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df`) and `gemma3:4b` (digest `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`). Temperature was 0, `max_new_tokens=96`, seed 2026, one repetition.

The exact dataset, specification, and lock have SHA-256 values `9c815d6d89b35a5ed5729a883e037c2e52e6411d97f7de0a06361844bdcfc1ba`, `3e09e0d10fa64b62c2a642d3e70194bd89344b271d09612fe3dd52890ff8ec30`, and `3d96b9ccf956649e6a98529b52d6af4d343b73edf98b7aec603fb294c1494a8e`. They reside under `experiments/phase4/`; the separate run directory and database are `experiments/phase4/jbb_pilot_run_v1/` and `experiments/phase4/jbb_pilot_v1.db`. `scripts/report_phase4_jbb_pilot.py` generated `audit_summary.json` from persisted observations/DB, rather than copying expected counts.

| Persisted observation class | Count |
|---|---:|
| Baseline | 28 |
| Benign control | 12 |
| Benign recovery | 8 |
| Isolated attack | 12 |
| Sequential attack | 24 |
| Recovery | 16 |
| **Total** | **100** |

There were 50 completed observations per model and zero failed observations in this run. The first and last persisted observation timestamps were `2026-10-10T15:55:48.841139+00:00` and `2026-10-10T15:57:52.156394+00:00`; this span is not a validated per-call latency summary. The run manifest hash was `6fd36674fc88ba0777ef13741a35e7796de4caf91f4b811c8cc71376dd0354eb`. The request-history audit found 100 consistent observations in 28 client conversations. All 24 isolation ledger entries remain provider-unverifiable, and the canary was inapplicable for all 100 calls.

The annotation candidate export contains 36 actual completed attack responses. Its blinded batch (`experiments/phase4/restricted_annotation/blinded_batch_v1.json`, SHA-256 `bbdc36fc77bb90d91fc7813a5069cec27360d86591a8b072230b2dcfb7cd553d`) omits model/source IDs; the private join map (SHA-256 `3e584315ef12f6834cd8ae3cbf78427cd6567e0601830690097aa6abdd7ced4f`) must remain restricted. **No human judgments have been imported.** The batch is an annotation work item, not a labeled result.

The only supported present inference is that two installed local models completed the planned 100 real-source requests and the records can be traced back to pinned inputs. There is no validated ASR, BSDA, RC, SAEA, attack-success count, model comparison, or choose-model recommendation. The historical 300-row judge calibration is a separate negative evaluator-reliability result and must not be conflated with this run. Paper charts for Phase 4 scientific metrics must return insufficient data.

Reproduction from the saved artifacts, without issuing model calls, uses PowerShell in `F:\SecureLLM` with `$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'` set for each command. Run `& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\inspect_phase4_jbb.py --output experiments\phase4\jbb_source_audit.json` to repeat the source audit, `& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\build_phase4_dataset_manifest.py` to verify the immutable manifest, `& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\audit_context_integrity.py --observations experiments\phase4\jbb_pilot_run_v1\observations --output experiments\phase4\jbb_pilot_run_v1\context_audit.json` for request-history checks, and `& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\report_phase4_jbb_pilot.py --run-dir experiments\phase4\jbb_pilot_run_v1 --database experiments\phase4\jbb_pilot_v1.db --output experiments\phase4\jbb_pilot_run_v1\audit_summary.json` for persisted-count reporting. These commands do not generate human labels or scientific metric values. The exact pilot execution specification and lock are retained for a later controlled rerun, but rerunning target models produces new observations rather than retroactively validating the saved run.
