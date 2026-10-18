# Phase 4 context and isolation audit

The runner persists every ordered request history, message identifiers, provider metadata, client conversation identifier, turn condition, and failure state. `core/experiments/context_audit.py` checks terminal roles, unique message IDs, provider-reported message counts when present, history-prefix continuity in each lane, duplicate turns, continuation after failure, and client conversation-ID reuse across lanes. Run `scripts/audit_context_integrity.py` to reproduce the audits. This proves consistency of the **sent request records**, not what a model attended to internally.

| Audit artifact | Observations | Client conversations | Result | Provider isolation |
|---|---:|---:|---|---|
| `experiments/phase4/phase3b_context_reaudit.json` | 50 | 14 | Request history consistent | Unverifiable from request history |
| `experiments/phase4/jbb_pilot_run_v1/context_audit.json` | 100 | 28 | Request history consistent | Unverifiable from request history |

The original Phase 3B ledger's 12 `isolation_unverifiable` records and the Phase 4 pilot's 24 are **not** proof of contamination. Distinct client IDs and complete messages reduce one class of bookkeeping error, but local Ollama metadata does not establish cache bypass, provider session separation, or effective model attention. No provider-specific cache isolation claim is made. The context status `retained` in the operational audit indicates that message length/count checks passed; it is not a context-retention proof. Canary checks were deliberately disabled for the real-source pilot because modifying the official attack prompts would confound that narrow experiment; this also removes canary evidence.

The audit must not relabel `isolation_unverifiable` as `verified`. If an actual shared session/handle or ledger `ISOLATION_SUSPECTED_LEAK` is found, the existing SAEA computation blocks the matched delta with `control_contamination_suspected`. Any source-only contrast that depends on unverified provider isolation requires a limitation statement and sensitivity treatment; a confirmatory isolation claim needs provider evidence or a validated external check. The saved request histories are auditable but contain restricted attack text and model responses and should not be indiscriminately published.
