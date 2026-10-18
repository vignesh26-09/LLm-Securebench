# Feasibility pilot novelty ledger — Gate 1 initialization

**Status:** 2026-10-13 requirements-stage assessment only. No delayed-secret feasibility-pilot observations exist in this ledger. `unsupported` does not mean the hypothesis is false; it means the required comparison has not been observed. Existing code and historical pilots do not, by themselves, establish research novelty. Literature comparison against verified publications remains pending; no priority claim is made.

| Claim ID | Claim (precise wording) | Status | Evidence required | Evidence so far | What would kill it | Phase that tests it |
|---|---|---|---|---|---|---|
| C1 | Delayed post-attack disclosure risk is distinguishable from immediate multi-turn attack success. | unsupported | Matched experiments showing delayed disclosure analysis adds reproducible information beyond immediate ASR or an equivalent existing metric. | 2026-10-13 code audit: `core/evaluation/attack_outcome.py` calculates immediate classified-only ASR; `core/experiments/runner.py` has no delayed-secret final-probe outcome. Historical Phase 3B/4 observations use another protocol; no C1 contrast artifact. | Delayed disclosure is fully explained by immediate ASR or an equivalent existing metric, with no substantive interpretive difference. | Approved phases 1, 6 and 7: literature, bounded pilot and same-observation metric comparison. |
| C2 | Topic-matched benign and refusal-history controls change the estimated adversarial effect compared with a generic benign control. | unsupported | Paired goal-level effect estimates under A–T, A–R and A–B1 with meaningful differences and adequate uncertainty; prespecified matching and no post-treatment selection. | 2026-10-13 code audit: `core/experiments/models.py` has a generic benign-control condition, but no versioned T/R/B1 arms for this secret-disclosure question. No C2 effect estimates. | Controls yield equivalent interpretations within adequately precise uncertainty bounds, or the comparison cannot isolate the claimed effect. | Approved phases 1, 4, 6 and 7: literature, arm construction, pilot and contrasts. |
| C3 | Excess disclosure risk varies with context distance in a manner not fully explained by truncation or dilution. | unsupported | Prespecified `d=0,2,5` interventions, token-distance controls, model-specific rendered-context/retention evidence and paired effects. | 2026-10-13 code audit: `core/inference/ollama_provider.py` records prompt-token count and a request-history-based context status; `docs/PHASE4_CONTEXT_INTEGRITY.md` says this does not prove effective retention. No distance-intervention artifact for this question. | Distance effects disappear after accounting for context placement and token distance, or context retention cannot be verified. | Approved phases 1, 2, 5, 6 and 7: literature, provider verification, distance control, pilot and analysis. |
| C4 | Evidence-gating prevents at least one unsupported conclusion that a naive analysis would have reported. | unsupported | A reproducible, prespecified naive-versus-gated reporting comparison showing a substantive difference in a claimed conclusion. | 2026-10-13 code audit: `core/reporting/charts.py` rejects noneligible chart records and `core/experiments/trajectory.py` preserves unavailable behavioral states. These are implementation evidence only; no same-data naive-versus-gated conclusion comparison for this study. | Eligibility gates make no meaningful difference to reportable conclusions or merely duplicate ordinary error handling. | Approved phases 1, 6 and 7: literature, pilot gate results and controlled reporting comparison. |

The allowed status vocabulary is `unsupported`, `plausible`, `supported by pilot`, `refuted`. At this stage all four remain unsupported. A later refutation must stay visible in this ledger with its evidence path and date. Scripted-history observations cannot be pooled with live observations to promote any claim.

## G0 review — 2026-10-14

**Decision: passes the Phase 0 source-and-evidence-class gate; STOP before Phase 1 pending separate user approval.** P0.1 source comparison is recorded in [`metric_code_audit.md`](metric_code_audit.md); P0.2 source/artifact inventory and read-only metadata checks are recorded in [`repository_baseline.md`](repository_baseline.md). The source functions implement paired BSDA displacement, behavioral-state recovery and sequential-versus-isolated deviation, not final exact-secret disclosure. Historical engineering, exploratory and external-calibration artifacts retain their own evidence classes. Unknown scorer validity, model rendering/retention and incomplete historical per-record hash re-audit are explicit in those documents; none was silently promoted to a pilot outcome. G0 therefore found no existing metric or record redefined as the proposed delayed-disclosure outcome. This is a code/evidence-class finding, not a literature novelty assessment or scientific validation.

| Claim | Status after G0 | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `metric_code_audit.md` §§BSDA/RC/SAEA and reconciliation; `repository_baseline.md` evidence table | Existing metrics do not calculate the proposed final exact-disclosure contrast, but no controlled delayed-versus-immediate empirical comparison or Phase 1 literature review exists. |
| C2 | `unsupported` | `repository_baseline.md` runner and evidence-class rows; `core/experiments/models.py::ExperimentalCondition`; `core/experiments/runner.py::_run_case` | Historical benign/sequential lanes are not the proposed topic-matched T/R/B1 controls; no paired new-arm observations or effect comparison exist. |
| C3 | `unsupported` | `repository_baseline.md` inference/context rows; `core/inference/ollama_provider.py::generate_conversation`; `core/experiments/context_audit.py::audit_request_histories` | Sent-history/token-window evidence does not verify rendered-context retention or a controlled 0/2/5-distance effect. |
| C4 | `unsupported` | `repository_baseline.md` persistence/reporting rows; `core/reporting/charts.py::_is_real` | Existing provenance gates are software safeguards; no prespecified same-data naive-versus-gated conclusion comparison exists. |

Passing source inspection or implementation tests alone does not change any claim status. The next permitted activity is only after the user's explicit Phase 1 approval.

## G1 review — 2026-10-14

**Decision: verified material overlap; STOP before Phase 2.** The dated [source ledger](prior_work_sources.md), [method matrix](prior_work_comparison.md), and [decision](prior_work_decision.md) document P1.1–P1.3. Full methods in the [JAMA delayed medical-injection study](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2842987), [AgentSecBench](https://arxiv.org/html/2605.26269v1), [PrivDrift](https://arxiv.org/html/2609.30094v2), and [EMNLP prompt-leakage study](https://aclanthology.org/2024.emnlp-industry.94.pdf) show material overlap in delayed legitimate-task effects, paired exact-marker security contrasts, secret-distance testing and multi-turn prompt leakage respectively. They do not establish an exact equivalent of the full proposed seven-arm study. An independent second reviewer has not signed the source/method coding; several full methods remain unverified, so no global originality or absence claim is made. The verified overlap warrants reducing broad novelty framing before implementation even though the precise combined hypothesis remains untested.

| Claim | Status after G1 | Evidence references | Reason for change or no change |
|---|---|---|---|
| C1 | `unsupported` | `prior_work_comparison.md` LEAK/MED/PRIV rows; `prior_work_decision.md` C1 row | Delayed attack influence and multi-turn leakage have prior art; the proposed non-requesting final exact-disclosure versus immediate-ASR comparison has no project observation. Narrow framing, but literature overlap does not empirically refute the precise claim. |
| C2 | `unsupported` | `prior_work_comparison.md` MED/ASB rows; `prior_work_decision.md` C2 row | Matched controls and paired advantage are prior art; T/R-vs-B1 effect sensitivity is not tested by project data. Do not promote from design alone. |
| C3 | `unsupported` | `prior_work_comparison.md` PRIV/MED rows; `prior_work_decision.md` C3 row | Secret-distance and delayed-persistence testing have prior art; context-valid A–T excess effects beyond truncation/dilution remain unobserved here. |
| C4 | `unsupported` | `prior_work_decision.md` C4 note; G0 implementation evidence | Phase 1 generated no naive-versus-gated same-data conclusion comparison. |

No status change is justified by literature review or documentation alone. Next gate requires explicit user review of the claim reduction and source-verification limitations; Phase 2 was not begun.

## G1 research-scope amendment review — 2026-10-14

**Disposition: proposed narrow framing; G1 remains STOP.** The [research-scope amendment](research_scope_amendment.md) proposes investigating unsolicited exact disclosure of a trusted synthetic secret during a later legitimate, non-secret-requesting task after a live adversarial **user** history, compared with matched non-adversarial histories. It explicitly credits [JAMA's later legitimate-task effect](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2842987), [PrivDrift's delayed secret/topic-distance test](https://arxiv.org/html/2609.30094v2), [AgentSecBench's exact-marker paired advantage](https://arxiv.org/html/2605.26269v1), and [Agarwal et al.'s multi-turn prompt leakage](https://aclanthology.org/2024.emnlp-industry.94.pdf). The proposal does not amend approved requirements/design, resolve remaining `NV` method cells, supply independent reviewer sign-off, or generate a pilot observation. A final secret repetition after earlier disclosure stays in `Y_final` but cannot be called a new delayed compromise. No originality claim for the individual ingredients is retained.

| Claim | Status after amendment review | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `research_scope_amendment.md` candidate framing, earlier-disclosure section and C1 falsifiers; `prior_work_decision.md` | The narrower same-observation final-versus-immediate comparison is proposed but unexecuted; prior delayed effects preclude broad novelty framing. |
| C2 | `unsupported` | `research_scope_amendment.md` control/mechanism and C2 falsifier sections; `prior_work_comparison.md` MED/ASB rows | Specific T/R-versus-B1 sensitivity has no eligible project observations; matched controls and paired contrasts already have prior art. |
| C3 | `unsupported` | `research_scope_amendment.md` context mechanism and C3 falsifier sections; `prior_work_comparison.md` PRIV row | The context-valid A–T distance interaction is unobserved and model-specific retention proof remains unresolved; distance testing itself has prior art. |
| C4 | `unsupported` | `research_scope_amendment.md` C4 falsifier; G0/G1 ledger entries | No prespecified same-data naive-versus-gated conclusion comparison exists. |

No status is promoted or refuted based on documentation. Explicit user approval and the amendment's independent G1 re-review checklist are required before Phase 2 can be reconsidered.

## G1 re-review of narrowed scope — 2026-10-14

**Decision: insufficiently verified; G1 remains STOP before Phase 2.** The [source-located re-review matrix](prior_work_comparison.md) examines trusted-item placement, attacker surface, live defender replies, final-task intent, earlier events, matched comparisons and context distance in the [JAMA full article and supplement](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2842987), [PrivDrift v2](https://arxiv.org/html/2609.30094v2), [AgentSecBench v1](https://arxiv.org/html/2605.26269v1), and [Agarwal et al.](https://aclanthology.org/2024.emnlp-industry.94.pdf). The [re-review decision](g1_rereview_decision.md) records the narrower candidate claim, the exact protocol overlaps and distinctions, and the remaining full-method checks. It does not establish global originality: the final SecReEvalBench journal methods and other material `NV` comparisons remain unverified. An independent second reviewer has **not** signed or dated a review, and the proposed scope has not been adopted into the approved requirements/design. No new scientific observations or human judgments were produced.

| Claim | Status after G1 re-review | Evidence references | Reason for change or no change |
|---|---|---|---|
| C1 | `unsupported` | `prior_work_comparison.md` re-review matrix, JAMA/PrivDrift/EMNLP rows; `g1_rereview_decision.md` claim check | The precise unsolicited trusted-secret final outcome is not established by the four described protocols, but delayed effects and multi-turn leakage have prior art. No project comparison of final versus immediate outcomes exists. |
| C2 | `unsupported` | `prior_work_comparison.md` matched-comparison row; `g1_rereview_decision.md` outstanding verification | JAMA and AgentSecBench already use controlled comparisons. No project A–T/A–R/A–B1 effect-sensitivity observation exists, and fine-grained JAMA payload matching remains unverified. |
| C3 | `unsupported` | `prior_work_comparison.md` context-distance row; `g1_rereview_decision.md` PrivDrift evidence | PrivDrift manipulates distance. No context-valid project A–T distance result or effective-retention verification exists. |
| C4 | `unsupported` | `research_scope_amendment.md` falsifiers; `g1_rereview_decision.md` verification boundary | Re-review and implementation checks provide no prespecified same-data naive-versus-gated conclusion comparison. |

No C1–C4 status changes are justified by this literature re-review. The unresolved source questions and absent authentic independent sign-off must remain visible; missing evidence is not coded as method absence. User review of this decision is required before any Phase 2 authorization.

## Focused G1 verification-completion review — 2026-10-14

**Decision: STOP; further source verification required before Phase 2.** The [source ledger](prior_work_sources.md) now distinguishes the final [SecReEvalBench journal record](https://doi.org/10.1016/j.neunet.2026.109065), its complete [earlier v2 manuscript](https://arxiv.org/pdf/2505.07584v2), the [withdrawn v3 notice](https://arxiv.org/abs/2505.07584), and [author scripts](https://github.com/VeraaaCUI/SecReEvalBench). The final journal full methods were inaccessible here, and the withdrawal explicitly records major rework; earlier methods/code cannot settle final-version comparison cells. The [current method matrix](prior_work_comparison.md), [reviewer package](g1_verification_package.md), and [G1 decision](g1_rereview_decision.md) record additional full-method overlap, exact `[needs verification]` items, and **no independent reviewer sign-off**. This pass generated no project observations or human judgments.

| Claim | Status after this dated review | Evidence references | Reason for change or no change |
|---|---|---|---|
| C1 | `unsupported` | `prior_work_comparison.md` SEC/MULTI/CRES rows; `g1_verification_package.md` nine-question SEC check | Sequence-aware unsafe/refusal timing and multi-turn attacks are verified prior art. The project has no same-observation immediate-versus-unsolicited-final exact-disclosure comparison; final SecReEvalBench method remains unverified. |
| C2 | `unsupported` | `prior_work_comparison.md` MED/ASB/DOJO/SEC control rows; `g1_verification_package.md` | Controlled comparisons exist in prior work, but the proposed T/R/B1 sensitivity has no eligible project data, and SEC journal matched-control details remain unknown. |
| C3 | `unsupported` | `prior_work_comparison.md` PRIV/SEC/MULTI distance rows; `g1_verification_package.md` | Prior sequence and distance manipulation do not establish a project context-valid A–T distance effect. The final SEC distance method is unverified. |
| C4 | `unsupported` | `research_scope_amendment.md` C4 falsifier; `g1_verification_package.md` verification boundary | Literature/code inspection is not the prespecified same-data naive-versus-gated conclusion comparison. |

All four claim statuses remain unchanged. No implementation test, documentation refinement or incomplete literature search is grounds for promotion. Independent human source review and the unresolved final-method checks remain mandatory before G1 can be reconsidered.

## G2 limited-engineering review — 2026-10-14

**Decision: G2 is not passed; STOP dependent Phase 3 implementation and all model calls.** The user's 2026-10-14 accelerated-pilot request separately authorized a *limited engineering feasibility continuation* despite the unresolved G1 originality stop. P2.1–P2.3 therefore produced read-only provider metadata, opt-in top-p transport, and a separate scientific context-status contract. The [provider audit](provider_audit.md) records installed Qwen/Gemma digests, static-template hashes, Gemma's system-to-user role serialization, Qwen's opaque renderer, and `retention_unverifiable` for both models. The [decision register](implementation_decisions.md) has no approved restricted-storage, error/retry, arm-distance or token-control choices. No harmless live provider probe or real pilot call was authorized or run. The current source/test evidence cannot establish post-template retention or a trusted-role equivalence for Gemma. Thus P2.4 and the G2 acceptance requirements remain incomplete.

| Claim | Status after G2 review | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `provider_audit.md`; `implementation_decisions.md` | No new controlled observations or delayed-versus-immediate comparison; G1 remains STOP for originality. |
| C2 | `unsupported` | `implementation_decisions.md` pending allocation/matching decisions | No approved T/R/B1 construction or empirical control comparison. |
| C3 | `unsupported` | `provider_audit.md` template/retention findings; `core/feasibility_pilot/context.py` | Static metadata and mock tests cannot verify rendered-context retention; Gemma role mapping is an unresolved threat to the trusted-instruction premise. |
| C4 | `unsupported` | P2 targeted tests and provider audit only | Code/test gates alone are not a same-data naive-versus-gated scientific conclusion comparison. |

This review neither overrides G1 nor refutes the hypotheses. It identifies the exact missing approvals and provider evidence before Phase 3 can start.

## G2 focused decision-package review — 2026-10-14

**Decision: P2.4 recommendations are reviewable but not approved; G2 remains pending and Phase 3 remains stopped.** The updated [implementation decision package](implementation_decisions.md) proposes an NTFS-isolated, encrypted, append-only restricted store; one strictly pre-submission retry at most; failure/null semantics; B0 distance `not_applicable` and diagnostic I/S distance cells; a secondary planned-token-distance control within the seven arms; and model-specific reporting that keeps Qwen rendering and Gemma trusted-priority limitations explicit. The [provider audit](provider_audit.md) remains the source for observed local metadata. No user choice, key custodian, methods reviewer sign-off, live probe or model run was obtained in this pass. Approval of these recommendations would permit only dependent engineering code and mock tests under the separately authorized limited continuation, not originality or a real pilot. Current provider evidence still yields `retention_unverifiable` for both models; Gemma's intended `system` priority remains unverified.

| Claim | Status after focused G2 review | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `implementation_decisions.md` retry and arm rows; `provider_audit.md` | Design choices are not controlled live observations or a delayed-versus-immediate comparison. |
| C2 | `unsupported` | `implementation_decisions.md` arm–distance and token-control rows | No A/T/R/B1 outcomes or matched effect comparisons exist; the approved primary A–T estimand is unchanged. |
| C3 | `unsupported` | `provider_audit.md`; `implementation_decisions.md` context-evidence rule | No verified post-template effective-retention evidence or distance-effect observations exist; Gemma priority remains a separate unresolved threat. |
| C4 | `unsupported` | `implementation_decisions.md` null-preservation rules | A proposed reporting gate is not the prespecified same-data naive-versus-gated conclusion comparison. |

This is a dated no-change novelty review, not G1 clearance, G2 sign-off or scientific validation. The next operation is explicit review of the Phase 3 coding decisions; all real model calls remain separately gated.

## G2 authorization record — 2026-10-14

The user's explicit “Phase 3 Authorization” message accepted the [G2 engineering decision package](implementation_decisions.md) for **limited P3.1–P3.4 coding only**. This is an authentic user authorization, not fabricated independent reviewer sign-off, G1 originality clearance, a model-call approval, or a protocol lock. The previously documented Qwen rendering and Gemma system-to-user serialization limits remain unresolved. C1–C4 remain `unsupported` because decision approval is not empirical evidence.

## G3 Phase 3 engineering review — 2026-10-14

**Recommendation: engineering G3 pass for user review; STOP before Phase 4 pending explicit G3 approval.** P3.1–P3.4 now have an NTFS ACL-isolated, AES-256-GCM encrypted and DPAPI CurrentUser-keyed append-only store; per-trial frozen-distribution secret binding; a versioned exact-contiguous checker with null-preserving outcomes; and separate development/held-out fixture files. The [checker gate artifact](../../../experiments/feasibility_pilot/checker_gate.json) reports 20/20 critical positives, 20/20 critical negatives and 85/85 broad held-out cases correct; sensitivity 35/35 and specificity 65/65 among 100 defined final outcomes, with 25 undefined cases retained separately. Fixture SHA-256 values are in that artifact. These are **fixture-only instrument checks**, not live model observations or semantic-leak validation.

Verification with `TEMP=TMP=F:\SecureLLM.tmp` and `F:\SecureLLM\.venv\Scripts\python.exe`: `-m pytest tests/test_feasibility_restricted_store.py tests/test_feasibility_secrets.py tests/test_feasibility_checker.py tests/test_feasibility_checker_gate.py -q` gave **19 passed**; `scripts/feasibility_checker_gate.py` exited 0 with the stated gate result; `-m pytest -q` gave **247 passed, 1 Starlette deprecation warning, 0 skipped**. Disposable security tests checked removal of inherited ACLs, key/raw separation, ciphertext-only disk storage, tamper and conflicting duplicate rejection, broad-file-ACL rejection, Git ignore, and secret rejection from public output. No Ollama generation, model download, seven-arm execution, or real trial-secret allocation occurred. The default restricted production directory was not initialized.

| Claim | Status after G3 review | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `core/feasibility_pilot/checker.py`; fixture gate artifact | Exact checker fixtures do not compare immediate and delayed live outcomes. |
| C2 | `unsupported` | `core/feasibility_pilot/secrets.py`; `implementation_decisions.md` | Fresh-secret and control-design safeguards produce no A/T/R/B1 effect estimates. |
| C3 | `unsupported` | `provider_audit.md`; `core/feasibility_pilot/context.py` | No new rendered-prompt or effective-retention evidence was obtained; no distance intervention was run. |
| C4 | `unsupported` | `core/feasibility_pilot/restricted_store.py`; checker gate artifact | Security and null-preservation tests are not the prespecified same-data naive-versus-gated scientific conclusion comparison. |

Remaining execution dependencies include independently reviewed goals/probes/scripts/tolerances, key custody and retention policy, model-specific context evidence, budget/preflight and separate real-call authorization. G1 remains STOP for research originality; implementation tests alone cannot promote any novelty claim.

## G4 Phase 4 engineering review — 2026-10-14

**Recommendation: engineering G4 pass for explicit user review; STOP before Phase 5.** The user's G3 acceptance authorized P4.1–P4.5 engineering only. Versioned goal and probe contracts, blinded two-reviewer/adjudication records, an append-only probe-version registry, the seven-arm applicability matrix, frozen A/T pair identities, planned-versus-realized matching contracts, six live mock-arm schedules, separately classed S replay, and an append-only mock attempt/observation ledger are implemented in `core/feasibility_pilot/`. The runner is deliberately **mock-provider-only**: no Ollama generation or real experimental arm was executed. The [probe-review contract](probe_review.md) and [numeric-matching contract](matching_tolerances.md) state that authentic reviewers, owner-approved exact wording, pilot goals/scripts and development-derived numeric tolerances are still absent. Phase 5's exact filler-exchange enforcement and scientific context-retention audit have not begun.

With `TEMP=TMP=F:\SecureLLM.tmp`, `F:\SecureLLM\.venv\Scripts\python.exe -m pytest tests/test_feasibility_probes.py tests/test_feasibility_allocation.py tests/test_feasibility_live_arms.py tests/test_feasibility_scripted_arm.py tests/test_feasibility_resume.py -q` gave **18 passed**. `F:\SecureLLM\.venv\Scripts\python.exe -m pytest -q` gave **265 passed, 1 Starlette deprecation warning, 0 skipped**. The mock tests execute all six live arms with provider-only assistant turns, execute S separately and exclude it from the live primary projection, verify append-only allocation and attempts, enforce one attested pre-submission retry maximum, leave uncertain/invalid intermediate failures with null outcomes, keep A/T pair IDs stable after failures/refusals, preserve earlier leaks, and find no trial secret in public observation files. These tests establish engineering behavior for fixtures, not empirical disclosure risks, validated probes, effective context retention or originality.

| Claim | Status after G4 review | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `core/feasibility_pilot/runner.py`; `tests/test_feasibility_resume.py` | Mock leak/earlier-leak fixtures are not controlled live delayed-versus-immediate observations. |
| C2 | `unsupported` | `core/feasibility_pilot/allocation.py`; `core/feasibility_pilot/matching.py`; `tests/test_feasibility_allocation.py` | Stable A/T pairing and planned matching do not supply empirical A/T/R/B1 contrasts. |
| C3 | `unsupported` | `matching_tolerances.md`; `provider_audit.md`; `core/feasibility_pilot/context.py` | Numeric tolerances and actual context-retention proof remain pending; no distance experiment was run. |
| C4 | `unsupported` | `core/feasibility_pilot/observations.py`; `tests/test_feasibility_resume.py` | Null-preserving mock tests are not a prespecified same-data naive-versus-gated scientific conclusion comparison. |

G1 remains **STOP for research originality**. No independent human source-review sign-off, authentic probe-review sign-off, pilot protocol lock or real-call authorization is inferred from this G4 engineering recommendation.

## G5 Phase 5 engineering review — 2026-10-14

**Recommendation: G5 engineering pass for explicit user review; STOP before Phase 6.** The user's G4 acceptance authorized P5.1–P5.2 only. `core/feasibility_pilot/distance.py` now freezes and validates exposure → exactly `d∈{0,2,5}` benign user/defender exchanges → final probe, while B0 remains distance-not-applicable and I/S remain diagnostic. The mock-only runner counts a filler only after a valid defender response, halts incomplete intermediate trajectories with null Y outcomes, and preserves the original assignment and pair identity. `core/feasibility_pilot/matching.py` adds a separately versioned secondary planned-token-distance control; `core/feasibility_pilot/context.py` and the append-only public audit record planned/observed counts, token usage, request-supplied model/template/`num_ctx` identity, each A/T counterpart's status and differential validity. The [Phase 5 audit](distance_integrity_audit.md) gives exact synthetic examples and limitations. No Ollama call, pilot goal selection, reviewer signature or real token-retention proof occurred.

With `TEMP=TMP=F:\SecureLLM.tmp` and `F:\SecureLLM\.venv\Scripts\python.exe`, the targeted command `-m pytest tests/test_feasibility_distance.py tests/test_feasibility_context_distance.py tests/test_feasibility_context.py tests/test_feasibility_resume.py -q` gave **23 passed**. The full command `-m pytest -q`, run after the last code change, gave **277 passed, 1 Starlette deprecation warning, 0 skipped**. These are mock-fixture engineering tests. The persisted Phase 5 mock audit rejects `retained_verified`; Qwen's final rendering and Gemma's trusted-priority limitation remain unverified. Known-truncated records and S replay cannot enter the verified-context live primary projection, while assigned coverage and observed operational outcomes remain visible.

| Claim | Status after G5 review | Evidence references | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `distance_integrity_audit.md`; `tests/test_feasibility_distance.py` | Exact mock spacing and null-preserving failures provide no live delayed-versus-immediate disclosure comparison. |
| C2 | `unsupported` | `core/feasibility_pilot/distance.py`; `core/feasibility_pilot/matching.py` | Preassigned controls and token schedules have no eligible empirical A/T/R/B1 observations. |
| C3 | `unsupported` | `core/feasibility_pilot/context.py`; `tests/test_feasibility_context_distance.py` | Synthetic truncation and unverified-retention classifications do not verify real effective context or a distance effect. |
| C4 | `unsupported` | `core/feasibility_pilot/observations.py`; `distance_integrity_audit.md` | Mock gating tests are not a prespecified same-data naive-versus-gated scientific conclusion comparison. |

G1 remains **STOP for research-originality claims**. Real goals, probe wording/review, approved numeric tolerances, provider instrumentation, model identity preflight, call budget and separate execution authorization remain external gates. G5 engineering acceptance would not authorize Phase 6 automatically or any model generation.

## P6.1 mock integration checkpoint — 2026-10-14

**Recommendation:** P6.1 engineering pass for explicit review only. The user accepted G5 and authorized P6.1, not P6.2 or real model calls. The [P6.1 verification report](p6_1_mock_verification.md) and [redacted smoke artifact](../../../experiments/feasibility_pilot/p6_1_mock_smoke.json) document a 12-assignment, seven-arm, mock-only trace, preserved null failures, separate scripted S, explicit mock provenance, context asymmetry and source hashes. Targeted tests: 34 passed; full suite: 282 passed with one existing Starlette deprecation warning. Zero real model calls or downloads. G1 remains **STOP**; the G6 pilot gate is not assessed.

| Claim | Status after P6.1 checkpoint | Evidence reference | Reason for no change |
|---|---|---|---|
| C1 | `unsupported` | `p6_1_mock_verification.md`; `tests/test_feasibility_e2e.py` | Deliberately scripted fixture outcomes are not live delayed-disclosure observations. |
| C2 | `unsupported` | Redacted smoke artifact; `core/feasibility_pilot/allocation.py` | Frozen mock A/T pairs do not estimate an empirical control-adjusted effect. |
| C3 | `unsupported` | `core/feasibility_pilot/context.py`; smoke pair rows | Synthetic known-loss and unverifiable classifications provide no actual effective-retention or context-distance effect evidence. |
| C4 | `unsupported` | `core/feasibility_pilot/observations.py`; P6.1 provenance tests | Mock provenance and null-preservation checks are engineering safeguards, not a prespecified same-data scientific comparison. |

No claim status changed because implementation and regression tests cannot establish a research finding. P6.2 remains blocked on the decisions listed in the P6.1 report and requires separate authorization.
