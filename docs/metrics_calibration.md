# Metric calibration criteria and stored evidence

## Scope and allowlist

Initial gate: public-clean at a36d13b, clean working tree. Software completeness
is distinct from scientific calibration. No new inference, labels or experiments.
Only these files may change:

- docs/metrics_calibration.md
- docs/METRIC_BACKEND_API.md
- apps/api/metric_compute.py
- apps/api/metric_calibration.py (new)
- frontend/src/components/metrics/CalibrationDetails.tsx (new, metric-only)
- frontend/src/components/metrics/StoredMetricEvidence.tsx
- frontend/src/pages/ScientificReviewsPage.tsx
- tests/test_metric_calibration.py (new)
- frontend/tests/CalibrationDetails.test.tsx (new)

No shared component, router, auth, navigation, non-metric page, formula, raw run,
label or trace changes are allowed. The existing MetricReadiness component is
reused unchanged; existing cards remain Not established because no scientific
claim passes the documented gates.

## Phase 1: criteria versus evidence

Common criteria: docs/COMPONENT_VALIDATION_PHASE10D_FORMAL_SPEC.md:5 requires
PLAN, independent DATA, ANALYSIS, scoped REPLICATION and explicit CLAIM REVIEW.
Lines 69 and 71 forbid a numerical result or synthetic test automatically
establishing a claim. Sample sizes are study-specific (line 63); there is no
universal numerical acceptance threshold. Unassessed criteria remain unknown.
Counts below are a local snapshot, not calibration targets or independent units.

Evidence paths used below:
- DB = securellmbench.db, scientific_records/scientific_reviews (read-only queries).
- C = experiments/local-runs/canary/canary-20261018-035526/ (synthetic leak/injection).
- T = experiments/local-runs/canary-devtest/devtest-20261018-042016/ (retrospective split).
- P = experiments/local-runs/controlled/verification-20261017-232316/ (pilot and labels).
- O = experiments/local-runs/oracle-sanity/oracle-20261018-043342/ (construction check).

| Page | Criteria (doc:line) | Evidence / measured values | Met? | Missing evidence | Verdict |
|---|---|---|---|---|---|
| Scientific reviews | Component spec:5,69: claim-linked independent decision, plan, analysis, replication | DB: 0 reviews; P has annotation reports, not claim reviews | partial | Scope-bound evidence bundle and independent review decision | PARTIAL |
| BSDA | Component spec:21,23; PHASE6_VALIDATION_GATES.md:22: separate components, benign/perturbed controls, fixed bounds, replication | DB: 300 component records; P: three model pilots; T: V0 recall 2/35, FPR 0/55; V3 recall 28/35, FPR 25/55 | partial | Independent component-specific reference/calibration, paraphrase controls, frozen bounds and review | PARTIAL |
| Recovery | RECOVERY_CAPABILITY_IMPLEMENTATION_SPEC.md:75,96,276; component spec:25,27 | DB: 150 trajectories, 148 uncalibrated, 2 undefined | partial | Compatible external positive applicability floor, validated state/probe/control study and review | PARTIAL |
| SAEA | SAEA_IMPLEMENTATION_SPEC.md:111,113; component spec:31 | DB: 150 records, 147 applicable, 2 failed_evaluation, 1 undefined | partial | Matched isolated/randomized controls, provider isolation/context evidence, versioned study and review | PARTIAL |
| DRAA | DRAA_IMPLEMENTATION.md:5,58; component spec:33: Mode A/B fidelity only | DB: 260 uncalibrated records; C: 180 outputs, 70 objective unsafe; T weak judge errors | partial | Independent scoped fidelity/missingness/provenance audit and review; scalar risk has no approved estimator | PARTIAL |
| PRI | PRI_IMPLEMENTATION.md:3,23; component spec:35: profile fidelity/coverage only | DB: 15 uncalibrated profiles; scalar/ranking absent | partial | Profile compatibility/composition study, audited reference coverage and review; no scalar estimator | PARTIAL |
| DQI | dataset-quality.md:14; component spec:11,13 | DB: 3 unavailable aggregate records with measured components | partial | Semantic embeddings for total; independent quality targets, external validity/sensitivity study and review | PARTIAL |
| Hallucination lift | MATCHED_CONTEXT_HALLUCINATION_LIFT.md:21,25,51 | DB: 0 factual pairs; P attack/LLM labels and C canary outcomes are different estimands | no | Context-valid matched factual pairs, frozen references, independent factual labels/adjudication and protocol | NEEDS_NEW_DATA |
| ML prediction | ML_PREDICTION_IMPLEMENTATION.md:17,20; component spec:37 | DB: 15 blocked readiness records; P labels lack eligible training target/split | no | Independent target labels, admissible features, grouped/temporal holdouts, baselines and calibration study | NEEDS_NEW_DATA |
| Statistics | STATISTICAL_VALIDATION_IMPLEMENTATION.md:14,19,31; component spec:39,49 | DB: 15 descriptive summaries; T retrospective split; P enriched human sample | partial | Frozen estimand/design/missingness plan, dependence-aware inference, replication and explicit claim review | PARTIAL |

Verdicts: CAN_ESTABLISH_NARROW=0, PARTIAL=8, NEEDS_NEW_DATA=2, NO_CRITERIA=0.
No criteria or numeric thresholds are invented or proposed: existing documents
already supply qualitative eligibility gates. Stored record counts only establish
availability, not independence, calibration compatibility, or scientific validity.

## Interpretation and measurement contract

The API adds `calibration` without removing existing response fields. It contains
status, scope, criterion text/met/measured_value/threshold/source_path, missing
evidence, and source measurements. Criteria may pass individually while the
scientific status remains not_established. Unknown is not failure or zero.
`scope` identifies descriptive evidence only unless every documented gate is met.
The current artifacts do not support an Established status, including narrow ones.

Canary counts and V0/V3 errors are recomputed from stored ground-truth/verdict
rows. Invalid verdicts are counted separately, never treated as safe. Rates with
empty denominators are null. The 90-row split is retrospective, not a true
holdout; the broader 180-output test is synthetic and restricted to leak/injection.
Oracle firing is a construction diagnostic, not an independent accuracy result.
Human and LLM annotations are explicitly distinct. The 30-row human check is
enriched toward non-safe candidates; no positive labels means recall unavailable.
It cannot calibrate factual-error outcomes, BSDA representations, RC or ML.

Only aggregate numbers, relative source paths and artifact hashes are exposed;
no prompts, responses, label rows, reviewer identities or credentials. Missing,
malformed, inconsistent or absent local artifacts get explicit unavailable reasons.
An installation without private run folders still renders the complete checklist.
API totals/ranges are engineering measurements across source records, not pooled
estimates of model safety. No cross-run mean or probability is manufactured.

## Verification

- Focused synthetic backend tests: 35 passed before the final pilot-count test.
- Full backend suite: 394 passed, 0 failed, 0 skipped (baseline 376).
- Full frontend suite: 68 passed, 0 failed (baseline 62); typecheck and lint passed.
- Authenticated runtime after repo-owned backend/frontend restart: all ten metric
  evidence endpoints returned HTTP 200 with calibration contracts, unavailable
  reasons and measured weak judge results. Health/ready/frontend and the four
  old-page API checks also returned 200. No model or benchmark calls.
- Current measured local artifacts: 180 objective canary outcomes, 70 non-safe;
  retrospective test n=90, 35 non-safe: V0 recall=2/35 (5.71%), FPR=0/55;
  V3 recall=28/35 (80%), FPR=25/55 (45.45%). Human check: 30 labeled,
  0 non-safe, so human-reference non-safe recall is unavailable.
- No metric became Established. Criteria/verdict counts remain 0 / 8 / 2 / 0
  for CAN_ESTABLISH_NARROW / PARTIAL / NEEDS_NEW_DATA / NO_CRITERIA.
- New tests cover individual met/unmet/unknown gates, explicit narrow scopes,
  missing/malformed artifacts, empty denominators, invalid judge exclusions,
  separate human/LLM evidence, pilot counts, old response-field preservation,
  all ten endpoints and frontend loading/error/empty states. No working shared
  component or non-metric page was changed.

## New objective experiment (2026-10-19)

Protocol: docs/OBJECTIVE_CALIBRATION_PROTOCOL.md, frozen before generation.
Aggregate source: data/calibration/objective_summary.json; raw outputs remain
gitignored under experiments/local-runs/calibration/20261019-150350.
This task's allowlist is the exact list in the objective protocol; shared and
non-metric behavior remains excluded. Existing calibration fields are preserved.

180 assigned fictional QA pairs across three models, 360 QA generations and
360 canary generations. There were 37 failed/incomplete canary generations;
323 completed oracle-labeled cases include 124 positives over 9 mixed template
groups. Thus the prespecified 30-positive/5-group engineering gate passed.

The fixed answer extractor rejected 97 QA responses; none became correct or
hallucination-free observations. Remaining outcomes were 72 correct and 191
explicit abstentions, with zero observed hallucinated extracted answers.
Complete-pair context proxy: Gemma unavailable (0/60), Qwen 0 [0,0] (44/60),
Llama 0 [0,0] (39/60). These are NOT canonical adversarial MCHL estimates and
abstention dominates the ungrounded arm. The Gemma absence is a negative result,
not zero lift. Scientific calibration remains Not established for all models.

Prompt-only synthetic oracle prediction, grouped OOF Average Precision:
- Template holdout: logistic 0.5033 [0.3516,0.6622], majority 0.2650
  [0.1554,0.4517]; paired difference CI [0.0945,0.3685].
- Model holdout: logistic 0.4024 [0.2890,0.5375], majority 0.3163
  [0.1863,0.4610]; paired difference CI [-0.0274,0.2296], so no clear improvement.
Recall/precision and all intervals/fold thresholds are retained in the aggregate
and panel. Ranking comparator uses training prevalence; majority decisions are
training-only hard-class choices. Group-dependent prevalence scores can give an
OOF baseline AP different from global prevalence. Constant-score ties are handled
as a whole threshold, never by arbitrary label ordering. CI resampling retains
whole template clusters but does not refit estimators or establish generalization.

One Windows state-file rename failure was resolved using the existing bounded
retry helper. All 310 already-saved case hashes and frozen prompt/QA/oracle
scoring functions were verified unchanged before resume. The immutable run
metadata was retained; a separate resume amendment records code hashes and the
AP tie-handling correction made before analysis. No case was regenerated.

Both pages now expose separate objective numeric evidence, with computation
prerequisites marked individually. Canonical MCHL still needs independently
checked factual labels and adversarial/matched-benign arms. ML results cover
only the synthetic oracle-emission target and do not establish a general safety
predictor. Independent study, replication and explicit claim review remain
missing. Neither page becomes Established.

Objective-work verification: full backend suite 410 passed / 0 failed / 0 skipped;
full frontend suite 70 passed / 0 failed. Typecheck and lint passed. Final panel
exclusion-count rendering was checked with affected frontend tests afterward.
All ten authenticated metric endpoints, health, ready, frontend and four old-page
API checks returned HTTP 200 after restarting only verified repo-owned listeners.
Diff scope: nine allowlisted files; raw run excluded from the staged index.
