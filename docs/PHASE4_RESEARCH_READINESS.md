# Phase 4 research-readiness decision

**Decision (11 October 2026): source integration and exploratory execution passed engineering checks; scientific validation and confirmatory publication claims remain blocked.** The complete 100-call run is real local inference but does not establish attack success or any model's safety.

| Gate | Current evidence | Decision |
|---|---|---|
| Licensed/versioned source | Pinned JBB behavior and official artifact revisions, local MIT notices and SHA-256, 100 harmful/100 benign source rows, 79 three-method-aligned indices. | Source-integrity gate passed for exploratory use; constituent-source redistribution review remains. |
| Leakage and grouping | Nine exact and 13 lexical-near historical calibration overlaps identified; selected indices 1/51 avoid both screens. | Local screen passed; global model-training/semantic leakage and production splits remain unresolved. |
| Controlled target execution | Two local models, two goals, one seed/repetition, 100/100 persisted completed observations. | Engineering feasibility passed; no statistical model comparison. |
| Context and isolation | Request histories consistent; 24 ledger entries `isolation_unverifiable`; no canary evidence. | Provider isolation and model attention not verified. |
| Human attack outcomes | 36 real responses exported to a blinded restricted batch; zero real labels imported. | ASR and attack-success statements blocked. |
| Behavioral states | Existing BSDA/RC/SAEA code and applicability guards, no validated Phase 4 state representations/calibration; harmful goals lack an independent legitimate task. | BSDA, RC, SAEA and any composite/ranking blocked. |
| Automated judge | Historical calibration: 300 source, 295 usable, TN 51 / FP 135 / FN 1 / TP 108, agreement 53.9%, κ≈0.211. | Not eligible as sole reference; no new target-domain validation. |
| Confirmatory protocol | Local exploratory lock only; no externally registered production design, precision rationale, grouped held-out split, or rater capacity commitment. | No confirmatory research claim. |

The next evidence-dependent actions are independent human annotation and adjudication of actual responses, validation of behavioral-state instruments and benign task matching, a grouped held-out source split, claim-specific evaluator error assessment, and a budgeted production protocol frozen before new confirmatory data. These are research gates, not UI toggles. Keep scientific result fields null and chart exports in `insufficient_data` state until they are met. The current work is suitable for a research-software/methods description and a separate historical judge-calibration negative result; empirical RQ1–RQ5 safety conclusions remain unavailable.

Verification on 11 October 2026: the seven new Phase 4 provenance/context/source-fetch tests passed; the full Python suite passed **203 tests** with one Starlette/httpx deprecation warning; API smoke returned 200 for health/ready and eight read resources and 201 for a fixture review; synthetic end-to-end smoke persisted/reloaded three fixture records. The pinned-source CLI verified seven local files without network access, and the manifest CLI reproduced the immutable source-manifest hash. The persisted historical calibration verifier recomputed 300 source/295 usable, TN=51, FP=135, FN=1, TP=108, coverage 98.333%, raw agreement 53.898%, and κ=0.211261. These verification results do not create Phase 4 human labels or measurement validation.
