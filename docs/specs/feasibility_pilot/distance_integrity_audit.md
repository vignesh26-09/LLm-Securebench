# Phase 5 mock distance and context-integrity audit — 2026-10-14

**Evidence class:** synthetic software fixtures only. No Ollama generation, approved pilot goal, authentic probe review, real model response or empirically verified retention was produced. The Phase 5 runner remains mock-provider-only.

## Versioned exchange schedules

`core/feasibility_pilot/distance.py` hashes each plan's frozen exposure, ordered filler steps and final probe under `exchange-distance-v1`. The schedule is append-only and linked to the frozen trial assignment before its first mock call. A live filler is counted complete only when its user message receives a valid defender-provider assistant response. The final probe is sent only after every assigned filler completes. B0 has no exposure, `distance=null` and zero fillers; I remains a diagnostic live arm; S has a tagged scripted exposure followed by **live** benign filler exchanges and stays outside the live A/T population.

| Synthetic test condition | Planned complete fillers | Completed fillers | Final response / outcome |
|---|---:|---:|---|
| A and T at `d=0` | 0 | 0 | Final probe follows exposure; fixture response completed. |
| A and T at `d=2` | 2 | 2 | Final probe follows exactly two defender-generated filler replies. |
| A and T at `d=5` | 5 | 5 | Final probe follows exactly five defender-generated filler replies. |
| A at `d=5`, fourth provider call length-limited | 5 | 2 | Third filler incomplete; no final probe; all three Y outcomes null. The paired T assignment remains in the denominator. |
| B0 | Not applicable | 0 | Final legitimate task only; no fictitious distance cell. |
| I at `d=5` | 5 | 5 | Neutral history and one isolated attack precede fillers; diagnostic only. |
| S at `d=2` | 2 | 2 | Secret-free scripted exposure is tagged; later filler replies are live mock-provider outputs; excluded from live primary projection. |

These fixtures use harmless placeholder tasks. They do **not** approve final wording or provide scientific outcome rates.

## Planned tokens, observed usage and status

`core/feasibility_pilot/matching.py::compare_token_distance_control` implements the predeclared **secondary** A/T-within-arm `d=2` versus `d=5` planned-token comparison. It requires the same model, goal, repetition, arm, probe version and script-library version plus a common frozen token-control group. A per-model tolerance must carry a development-evidence hash and owner approval before real execution. The test uses unapproved synthetic values: planned distances 100 and 103 tokens, fixture tolerance 5, and observed prompt-count proxy distances 20 and 50. It reports planned match and observed mismatch separately. Neither value reassigns the d=2 A/T primary pair or proves effective context retention. The observed proxy is `final prompt_eval_count − exposure prompt_eval_count`, **including the final probe**; it is not a measured input-token position and may be unavailable or affected by truncation.

`core/feasibility_pilot/context.py::audit_trial_context` records requested `num_ctx`, request-supplied model digest and static template hash, final and total provider-reported token usage, planned and completed exchange counts, planned token estimate, observed token proxy and the evidence basis. These identities are labeled `request_metadata_only_not_provider_verified` in mock audits. Qwen remains `rendered_prompt_unverified`. Gemma remains `rendered_prompt_unverified` with a separate `trusted_priority_unverified_system_to_user` limitation. Neither request continuity, a nominal context window, a token count nor a canary upgrades a trial to `retained_verified`.

The synthetic status tests distinguish a referenced known-loss fixture (`truncated_known`) from an uninstrumented completed fixture (`retention_unverifiable`). A synthetic positive retention assertion is downgraded to `retention_unverifiable` before persistence; the public mock audit store rejects any attempt to persist it as `retained_verified`. The A/T report shows both counterpart statuses, missing audits, completion asymmetry, per-arm truncated/unverifiable counts and differential-validity warnings. `verified_context_primary_rows()` requires a completed exact outcome and a separate affirmative non-mock context audit; therefore these mock fixtures produce **zero** verified-context primary rows. An observed exact outcome in a known-truncated trial remains in the all-assigned operational record, not the verified-context subset.

## Open scientific and operational limits

No model-specific approved tokenizer/template rendering, numeric tolerance, token-control filler scripts, effective-retention instrument, exact pilot goals/probes, authentic review signatures, budget/preflight lock or real-call authorization exists here. Mock tests establish failure handling and classification boundaries only. A requested `num_ctx` or static `/api/show` template cannot prove that the protected instruction survived actual inference truncation, and Gemma's intended trusted priority remains unverified. Phase 6 is required for real-run preflight; it has not begun.
