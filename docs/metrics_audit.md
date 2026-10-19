# Metrics & Research audit

## Scope and gate

- Audited branch: `public-clean`; initial HEAD: `a69561feb6f3ff893ba9468dd7d55320455c124d`; initial tracked/untracked working-tree changes: 0.
- Phase 1 used source/spec/test inspection plus read-only SQLite inspection. Phase 2 added metric-only stored-evidence views and tests. No servers, network requests, model calls or downloads were used.
- Local database counts describe the inspected local database, not a fixture, a published dataset, or scientific validation. No rows, prompts, responses, account details, or labels are reproduced.
- Before counts: COMPLETE 0, PARTIAL 8, STUB 0, BLOCKED 2. After implementation/checks: COMPLETE 8, PARTIAL 0, STUB 0, BLOCKED 2. COMPLETE describes software/page functionality, not scientific calibration or production suitability.
- A working formula/calculator is distinct from a completed metric page and from established scientific calibration. Existing workbenches accept measured JSON, call real engines, and explicitly save engineering-only records.

## ALLOWLIST for subsequent implementation

Only the following exact paths may be edited. New files are marked `(new)`. Inclusion is permission for this task's metric-only work, not a requirement to change the file.

1. `docs/metrics_audit.md`
2. `docs/METRIC_BACKEND_API.md`
3. `frontend/src/pages/MetricPages.tsx`
4. `frontend/src/pages/ScientificReviewsPage.tsx` (new, reviews-only wrapper)
5. `frontend/src/components/metrics/StoredMetricEvidence.tsx` (new, used only by the audited metric pages)
6. `frontend/tests/MetricPagesAudit.test.tsx` (new)
7. `frontend/tests/ScientificReviewsPage.test.tsx` (new)
8. `apps/api/metric_compute.py` (metric routes only; no authentication changes)
9. `tests/test_metric_compute_api.py`
10. `tests/test_metric_dashboard_evidence.py` (new)
11. `frontend/src/App.tsx` (explicit user exception: one import plus the `/reviews` element only)

No core formula changes were necessary or allowlisted. Existing engines and existing shared components are reused unchanged. All other paths, including shared page/rendering components, auth, dashboard, run/result/history views, stylesheets, Grafana, raw runs, labels, and traces, are outside this allowlist.

**Shared-router exception approved by the user:** `frontend/src/App.tsx` is restricted to one `ScientificReviewsPage` import and the `/reviews` element. The exact expected file is checked against the pre-edit content. No other route, guard, provider, layout, navigation or sidebar was changed. The diff was shown immediately after editing.

## Page audit before implementation

`MP` means `frontend/src/pages/MetricPages.tsx`; its nine exports reuse the unchanged `ScientificRecordsPage`, `MetricReadiness`, and `MetricWorkbench`. `EP` means `frontend/src/pages/EntityPage.tsx`.
For metric calculators, `compute_metric` is in `apps/api/metric_compute.py`, exposed at `POST /metrics/compute/{metric}`; immutable engineering saves use `/save`. Saved records use `GET /scientific-records?family=...`; `GET /metrics/catalog` exposes record/status counts.

| Metric | Page file / export | Backend function | Before: Implementation / Scientific calibration | Gaps | Verdict |
|---|---|---|---|---|---|
| Scientific reviews | EP, selected by `/reviews` in App.tsx | `register_resources` review-resource listing; `internal_review` for explicit review persistence | No readiness card / no calibration card | Browser has loading/error/empty/pagination; readiness card absent; 0 explicit reviews. Needs wrapper routed only at `/reviews`; no numerical review chart warranted. | PARTIAL |
| BSDA | MP / `BSDAPage` | `compute_metric('bsda')` → `compute_bsda_with_adapters` | Implemented / Not established | 300 component-vector records, shown principally as payloads; no stored-component chart. Missing components need per-value reasons; component calibration is not established. Composite remains absent. | PARTIAL |
| Recovery capability | MP / `RecoveryPage` | `compute_metric('recovery')` → `RecoveryCapabilityEngine.evaluate_run` | Implemented / Not established | 150 trajectory records (148 uncalibrated, 2 undefined); no trajectory/deviation chart. RC indices require compatible external calibration; raw trajectories can still be displayed honestly. | PARTIAL |
| SAEA | MP / `SAEAPage` | `compute_metric('saea')` → `SAEAEngine.evaluate` | Implemented / Experimental | 150 records (147 applicable, 2 failed, 1 undefined); no sequential-vs-isolated chart. Calibration wording should be Not established; experimental status belongs in the reason. Missing/failed controls must remain excluded. | PARTIAL |
| DRAA | MP / `DRAAPage` | `compute_metric('draa')` → `core.draa.diagnostics.summarize` | Implemented (Modes A/B) / Not established | 250 descriptive records; evidence table exists but no appropriate stored-feature/count chart. Scalar risk is unavailable by specification, not an implementation gap. | PARTIAL |
| PRI | MP / `PRIPage` | `compute_metric('pri')` → `core.pri.diagnostics.summarize` | Implemented profile / Not established | 14 profile records; cells are inspectable but no coverage/profile chart. Missing categories/values must not become zero; scalar/ranking remains unavailable. | PARTIAL |
| DQI | MP / `DQIPage` | `compute_metric('dqi')` → `calculate_dqi` | Implemented diagnostic / Exploratory | 3 unavailable aggregate records; component summary exists, chart absent. Show measured components only; unavailable semantic embeddings/total need explicit reason. Calibration remains Not established; diagnostic status remains exploratory. | PARTIAL |
| Hallucination lift | MP / `MatchedHallucinationPage` | `compute_metric('mchl')` → `compute_matched_hallucination_lift` | Implemented calculation / Not established | 0 matched factual-pair records. Requires matched model/question/reference/configuration, context validity, independently checked factual labels and label references. Existing generic empty state is nonspecific; page explanation already names these requirements. No chart values can be supplied. | BLOCKED |
| ML prediction | MP / `MLPredictionPage` | `compute_metric('ml')` → `train_fixture_baselines` | Implemented pipeline / Blocked pending labels | 14 readiness records, all blocked; no eligible independent-target/features/group-split experiment. Existing formula strings/readiness records are not predictions. No performance chart may be invented. Calibration cannot be Established. | BLOCKED |
| Statistical analysis | MP / `StatisticalPage` | `compute_metric('statistics')` → `core.statistics.descriptive.summarize` | Implemented descriptive statistics / Not applicable | 14 real computed summaries; table exists, stored-measurement chart absent. Preserve source units, missing denominators, n=1 undefined variance, and descriptive-only interpretation. Do not imply scientific calibration. | PARTIAL |

## Specifications, core ownership, and existing test coverage

| Page | Core module / contract | Local specification | Existing tests inspected or identified |
|---|---|---|---|
| Scientific reviews | `core/persistence/service.py`, scientific review entity/repository | `docs/BACKEND_API_PHASE11_IMPLEMENTATION_RECONCILIATION.md`; `docs/STATISTICAL_VALIDATION_IMPLEMENTATION_RECONCILIATION.md` | `tests/test_resource_api.py`, `tests/test_metric_compute_api.py` (review not a calculator); `frontend/tests/EntityPage.test.tsx`; no reviews-specific readiness-card test |
| BSDA | `core/metrics/bsda.py`, `core/metrics/bsda_adapters.py` | `docs/METRIC_DEFINITIONS.md:8`; `docs/METRIC_BACKEND_API.md:11` | `tests/test_bsda_adapters.py`, `tests/test_metric_compute_api.py`; `frontend/tests/ScientificIntegrity.test.tsx`, `MetricWorkbench.test.tsx` |
| Recovery | `core/recovery/engine.py`, `models.py` | `docs/RECOVERY_CAPABILITY_IMPLEMENTATION_SPEC.md`, especially sections 1–3 and 7 | `tests/test_recovery.py`, `tests/test_metric_compute_api.py`; no dedicated saved-trajectory page-chart test |
| SAEA | `core/saea/engine.py`, `models.py` | `docs/SAEA_IMPLEMENTATION_SPEC.md`, `docs/METRIC_DEFINITIONS.md:10` | `tests/test_saea.py`, `tests/test_metric_compute_api.py`; `frontend/tests/ScientificIntegrity.test.tsx` |
| DRAA | `core/draa/evidence.py`, `diagnostics.py`, `models.py` | `docs/DRAA_IMPLEMENTATION.md`, `docs/DRAA_IMPLEMENTATION_RECONCILIATION.md` | `tests/test_draa.py`, `tests/test_metric_compute_api.py`; `frontend/tests/ScientificIntegrity.test.tsx` |
| PRI | `core/pri/profile.py`, `diagnostics.py`, `models.py` | `docs/PRI_IMPLEMENTATION.md`, `docs/PRI_IMPLEMENTATION_RECONCILIATION.md` | `tests/test_pri.py`, `tests/test_metric_compute_api.py`; `frontend/tests/ScientificIntegrity.test.tsx` |
| DQI | `core/dataset/quality.py` | `docs/METRICS.md`; `docs/METRIC_BACKEND_API.md:16` | `tests/test_metric_compute_api.py`, `tests/test_dataset.py`; `frontend/tests/DqiSummary.test.tsx` |
| Hallucination lift | `core/metrics/matched_hallucination.py` | `docs/MATCHED_CONTEXT_HALLUCINATION_LIFT.md` | `tests/test_matched_hallucination.py`; `frontend/tests/ScientificIntegrity.test.tsx` |
| ML prediction | `core/prediction/training.py`, `admissibility.py`, `splitting.py`, `metrics.py` | `docs/ML_PREDICTION_IMPLEMENTATION_RECONCILIATION.md`, sections 5–11, 15–16 | `tests/test_prediction.py`, `tests/test_metric_compute_api.py`; existing workbench tests are not evidence of predictive quality |
| Statistics | `core/statistics/descriptive.py`, method-specific modules | `docs/STATISTICAL_VALIDATION_IMPLEMENTATION_RECONCILIATION.md`; `docs/METRIC_BACKEND_API.md:18` | `tests/test_statistics_basic.py`, `test_statistics_planning.py`, `test_statistics_remaining.py`, `test_metric_compute_api.py`; `frontend/tests/MetricWorkbench.test.tsx` |

## Existing UI and API safeguards

- `ScientificRecordsPage` already renders loading/error states, record pagination, calculators, full payload inspection, and provenance badges. These are reusable, not stubs.
- `MetricWorkbench` validates JSON shape, forwards real compute/save requests, displays calculation/save errors and busy state, and labels caller-supplied results engineering-only. No model calls are required for these calculators.
- `RecordTable` preserves source status/schema/scope/provenance. `EvidenceSummary` has DRAA/PRI/statistics tables; DQI has its own component summary. None supplies the missing page-level stored-evidence charts.
- No live-value hardcoded demonstration numbers were found in these metric page definitions. Synthetic numerical examples in unit tests are legitimate tests, not dashboard evidence.
- Calibration checks remain insufficient: no inspected family has a provenance claim of established scientific validity; no Recovery payload contains a nonempty calibration artifact. A caller-supplied calibration object is not independent verification.
- Existing 30-row human check has no non-safe labels and is not a BSDA, RC, DQI, PRI, or SAEA calibration study. It cannot unlock these cards.
- DRAA scalar values are null in all 250 records; PRI scalars are null in all 14 records. Specifications explicitly prohibit inventing the missing estimators.
- Older reconciliation docs may describe historically deferred runtimes. Current implementation and the metric-specific reconciled contracts take precedence over historical implementation-status prose; scientific eligibility still follows the stated evidence gates.

## Sidebar highlight finding

`frontend/src/components/shell/Sidebar.tsx:10` uses React Router `NavLink`, which supplies `active` for the matching route. It does not inspect metric implementation/calibration status. Recovery points to `/metrics/recovery`; Statistical analysis points to `/statistics`.
`frontend/src/studio.css:47` styles `.sidebar a.active` and `.sidebar a:hover` identically. Therefore the current route and a hovered different item can both look highlighted. No Recovery/Statistics-specific highlight or status flag was found.
Verdict: **not a sidebar-routing/status bug based on inspected source**. The exact pointer state of the earlier screen was not inspected. No shared sidebar/CSS edit is justified.

## Minimal implementation plan and approval boundary

1. Keep all formulas, missingness rules, DRAA/PRI null scalars, auth and shared components unchanged.
2. Add metric-only stored-evidence projection/rendering and appropriate charts using real persisted observations; preserve per-record source/status/units and explicit unavailable reasons. No fresh inference or evidence generation.
3. Keep missing ML/MCHL measurements BLOCKED. Do not infer calibration from a record count, a synthetic test, a judge verdict, or the small human check.
4. Add focused synthetic backend/page tests for projections, null/failed exclusions, source provenance, page states and status cards.
5. Scientific reviews requires a new reviews-only wrapper that reuses the unchanged `MetricReadiness` and `EntityPage` components. Connecting it requires these two shared-router-only changes in `frontend/src/App.tsx`: import `ScientificReviewsPage`; change only the `/reviews` element from `EntityPage(...)` to `ScientificReviewsPage`. No other route or auth condition would change.
6. The user's hard rule required pausing before a shared-file change. Permission was obtained for the exact two-line router exception above. Existing shared components/utilities and all other router content remain unchanged.

## Verification / final status

- Backend full suite, once: **376 passed / 0 failed / 0 skipped** (baseline 358). New synthetic tests cover nine families, failed/missing states, invalid numeric values, provenance redaction, immutable read-only projection, family aliases, pagination and unchanged API protection.
- Frontend full suite, once via `cmd /c npm.cmd test -- --run` with UTF-8 capture: initially **61 passed / 1 failed**. The existing empty-record test reuses one Response object for multiple requests. The new metric-only reader now clones its response before reading it; no old test or shared fetch utility was changed.
- Affected frontend rerun only (`MetricWorkbench`, new metric-page audit, `ScientificIntegrity`): **24 passed / 0 failed**. Final coverage: **62 distinct tests, no unresolved failure** (requested baseline 58; earlier pre-change actual count was 44). New reviews-only tests passed in the full run.
- Frontend typecheck and lint passed. No full-suite rerun, model inference, network request, server start or download was needed.
- Read-only inspection exercised projections against existing saved records: BSDA 300/300 records with finite evidence, Recovery 148/150, SAEA 147/150, DRAA 250/250, PRI 14/14, DQI 3/3 (components only), statistics 14/14, ML 0/14, MCHL 0/0. These are source-presence counts, not success rates or calibration evidence.
- The App.tsx diff contains only the approved import and `/reviews` element. Protected-file hashes and the exact change allowlist are checked before staging. No run/label/trace data is staged. A normal local commit is the final step; no push is performed.

## Final page verdicts

| Page | Final verdict | Result / remaining evidence requirement |
|---|---|---|
| Scientific reviews | COMPLETE | Reviews-only readiness wrapper reuses the unchanged browser; independent documented review evidence still needed for scientific calibration. |
| BSDA | COMPLETE | Stored component chart, source values, provenance and per-component unavailability; no composite or calibration upgrade. |
| Recovery capability | COMPLETE | Raw trajectory chart with null gaps and preserved failed records; RC indices remain unavailable without compatible external applicability calibration. |
| SAEA | COMPLETE | Valid per-step sequential-minus-isolated context-effect chart; failed or invalid-control points remain missing. |
| DRAA | COMPLETE | Actual feature-status counts with source inspection; scalar risk remains unavailable by specification. |
| PRI | COMPLETE | Declared category coverage and observed-cell chart; missing categories are not zeros; no scalar/ranking. |
| DQI | COMPLETE | Measured component chart; semantic novelty and aggregate remain unavailable without embeddings. |
| Hallucination lift | BLOCKED | Needs matched model/question/configuration/frozen-reference pairs, valid context, and independent factual-label references; no eligible saved pairs exist. |
| ML prediction | BLOCKED | Needs independent outcome labels, admissible features and a leakage-reviewed grouped split/eligible experiment; saved readiness records do not supply targets. |
| Statistical analysis | COMPLETE | Recorded descriptive measurements in source units, source table and provenance; no inferential or calibration claim. |

All ten pages now use **Scientific calibration: Not established**, with an explicit reason. No existing artifact was demonstrated to satisfy the independent criteria for Established. Blocked pages keep real calculators available for explicitly supplied qualified inputs but do not invent saved results.
