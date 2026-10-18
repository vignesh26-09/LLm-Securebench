# P6.1 mock integration verification — 2026-10-14

**Decision recommended:** P6.1 engineering pass for review. This is a disposable, harmless, mock-provider execution. It is not a real pilot, a scientific result, a model-safety comparison, or G1 originality clearance. C1–C4 remain unsupported. P6.2, P6.3, G6, and Phase 7 have not begun.

## Reproduction and evidence

From `F:\SecureLLM` in PowerShell:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& .\.venv\Scripts\python.exe scripts/feasibility_mock_smoke.py --output F:\SecureLLM.tmp\p61_mock_report.json
& .\.venv\Scripts\python.exe -m pytest tests/test_feasibility_e2e.py tests/test_feasibility_distance.py tests/test_feasibility_context_distance.py tests/test_feasibility_context.py tests/test_feasibility_resume.py tests/test_feasibility_restricted_store.py -q
& .\.venv\Scripts\python.exe -m pytest -q
```

The saved redacted snapshot is [`experiments/feasibility_pilot/p6_1_mock_smoke.json`](../../../experiments/feasibility_pilot/p6_1_mock_smoke.json), SHA-256 `1107ed29427613496aec7586c755b5fc031552498f024f41768c1b3cb9e48b07`. It contains only fixture identifiers, digests, statuses and counts. Its `source_sha256` entries cover the smoke script, runner, checker, context audit and distance scheduler; `approved_fixture_corpus_sha256` hashes the harmless planned text. Each run binds fresh random trial secrets and writes encrypted raw evidence to a disposable restricted directory, so ciphertext, timestamps and a newly generated report file are not expected to be byte-identical across reruns. The frozen allocation hash and source/corpus hashes are stable until the corresponding source changes.

`scripts/feasibility_mock_smoke.py` executed successfully with no application warning. After the final test change, the targeted command gave **34 passed, 0 failed, 0 skipped, 0 warnings** in 33.92 s. The full Python command gave **282 passed, 0 failed, 0 skipped, 1 warning** in 68.47 s. The warning is the existing `StarletteDeprecationWarning` from `fastapi.testclient` about `httpx` and `starlette.testclient`; no test failed. The new P6.1 test file contributes five tests.

## End-to-end mock trace

One frozen allocation contains 12 assignments across all seven arms `A/B0/B1/I/R/S/T`; B0 distance is not applicable, and the applicable distances are exactly 0, 2 and 5 complete benign user/provider exchanges. The smoke executes the approved state machines, a final ordinary-task fixture probe, a separate scripted S history, per-trial cryptographic secret binding, encrypted raw request/response records, exact checker, immutable public observations, context audits, and a redacted report. The script is guarded by the existing mock-only runner. Tests block socket connections and URL access, reject Ollama/download subprocess commands, and verify the only provider is the mock implementation. **Real model calls: 0; downloads: 0.**

Coverage: **12 assigned, 12 observed, 10 completed, 2 incomplete, 0 missing, 2 null final outcomes**. The two incomplete assignments are an interrupted request whose delivery is uncertain and an invalid intermediate filler response. Neither was retried as an attack result, marked non-leak, or removed from its assignment/pair denominator. One separately attested pre-submission failure was retried once with identical request bytes and the same bound secret. Resume of the interrupted attempt made no new provider call. Completed observations are immutable; a conflicting rewrite is rejected.

Checker fixture outcomes `(Y_final, Y_earlier, Y_ever)` include both `(1,1,1)`, final-only `(1,0,1)`, earlier-only `(0,1,1)`, and incomplete `(null,null,null)`. These are deliberately generated fixture strings, **not observed disclosure rates**. Live assistant history is reconstructed only from mock-provider response records; S has one explicitly scripted assistant turn and does not enter the six-row operational A/T projection. All observations now carry explicit `execution_provenance=mock_fixture`, separate from the arm-mechanism `evidence_class`. The verified-context scientific A/T projection contains **zero** mock rows.

Every trial has a context audit. The synthetic status fixture yields `retention_unverifiable=11`, `truncated_known=1`, and `retained_verified=0`; the known-loss status is based only on a labeled synthetic evidence reference. All three A/T pairs remain visible. Two show validity asymmetry, including one A incomplete/T completed pair; none is silently rematched or promoted to verified retention. The report contains per-pair statuses and an aggregate differential-validity warning. It does not infer that a real model retained or attended to context.

Secret-protection tests scan the redacted JSON, public observation files, public restricted-store projection, captured mock-provider logs and encrypted raw files for every generated secret. No match occurs. The public-safety gate also rejects a protected-secret-shaped string. Test exception messages and the report contain no trial secret. Raw prompts, responses and secrets exist only transiently in the ACL-isolated, encrypted disposable evidence root; the public snapshot stores none of them.

## Remaining P6.2 blockers

G1 remains **STOP** for originality; independently reviewed prior-art sign-off has not been obtained. P6.2 still needs owner-approved final 20 pilot goals and separate development goals, exact legitimate-probe wording and authentic two-reviewer/adjudication records, attack/benign/refusal/filler/S scripts, model-specific development-derived numeric matching tolerances, model digests/templates/settings/seeds, real context-rendering/retention evidence limits, access/key custody and retention decisions, complete call/time/storage budget, and an immutable analysis/protocol preflight lock. Real model calls require separate authorization after that preflight. Qwen final rendering and Gemma trusted-priority limitations remain unresolved. No mock output closes any of these decisions.
