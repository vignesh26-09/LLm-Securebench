# Metric computation API

The backend now exposes `GET /metrics/catalog`, `POST /metrics/compute/{metric}`
and `POST /metrics/compute/{metric}/save`.
The catalog reads current `scientific_records` counts and statuses; it does not
infer that a missing record has a numerical value. A signed-in workspace session
is required for computation when API authentication is enabled.

| Metric path | Existing source engine | Required POST body | Ordinary local run |
| --- | --- | --- | --- |
| `bsda` | `core.metrics.bsda.compute_bsda` | `value`: versioned `BSDAInput`; optional caller-supplied `calibration`, `semantic_adapter` (`lexical` or `none`) | Full platform runs create two matched pairs per source case |
| `recovery` | `RecoveryCapabilityEngine.evaluate_run` | `value`: `RecoveryRunInput`; optional `calibration` | Full platform runs create baseline/attack/recovery trajectories; indices remain uncalibrated without an artifact |
| `saea` | `SAEAEngine.evaluate` | `value`: `SAEAInput` with matched isolated controls and context status | Full platform runs create sequential/isolated observations and exploratory judge states, subject to context and measurement gates |
| `draa` | `core.draa.diagnostics.summarize` | `records`: nonempty list of `DRAAEvidenceRecord` | Mode A evidence is computed and persisted per completed evaluation |
| `pri` | `core.pri.diagnostics.summarize` | `profile`: `PRIProfileRecord` | Mode A profile is computed and persisted per run |
| `dqi` | `core.dataset.quality.calculate_dqi` | `dataset`: `Dataset`; optional `embeddings` and `weights` | Full platform runs calculate full-corpus components; semantic novelty/total require embeddings |
| `ml` | `core.prediction.training.train_fixture_baselines` | `experiment_id`, `task`, `schema`, `features`, `targets`, `manifest`, `logistic_config` | Readiness record is persisted; training needs independent labels and an admissible split |
| `statistics` | `core.statistics.descriptive.summarize` | `values`: finite observations | Latency summary is computed and persisted per run |

Each POST uses the existing typed scientific contract and calculation code. It
returns a source-native result/status, `evidence_class=ephemeral_supplied_input`,
`input_verification=caller_supplied_unverified`, and `persisted=false`. The
calculation does **not** write a scientific record or assert validation. A
caller-supplied calibration artifact may make the engine return a calibrated
component, but the API does not independently verify that artifact. The
wrapper therefore always reports `scientific_validation=not_established`.

`/save` runs the same calculation and appends its redacted output to
`scientific_records` with an immutable content-derived ID and
`reporting_class=engineering_only`. The dashboard's metric record pages can
then display it. Repeating the exact request returns HTTP 409 rather than
overwriting it. The source-input hash is retained, but the supplied prompts,
responses, and labels are not saved by this route. Paper-ready chart gates
exclude this engineering class.

The BSDA route uses the existing deterministic lexical adapter for a local
engineering semantic distance and the detector-native safety adapter. It does
not invoke a judge or claim a validated semantic representation. Its instruction
component remains unmeasurable unless the source contract can score the
supplied constraints; its composite remains null by design. For DQI, omitted
embeddings leave semantic novelty and any weighted total dependent on it
unavailable. For recovery, missing calibration preserves the raw attack
deviation and returns null RC indices. SAEA preserves null context effects
when an isolated control is missing or contaminated. ML preserves split and
feature admissibility checks and identifies synthetic-fixture baselines.

Example: a descriptive calculation, without model generation or database writes:

```http
POST /metrics/compute/statistics
Content-Type: application/json

{"values":[120.0,145.0,130.0]}
```

The user-facing benchmark route now requires all 10,000 verified source prompts,
an installed judge, and explicit full-workload confirmation. It uses the
checkpointed controlled pipeline described in [FULL_CORPUS_METRIC_EXECUTION.md](FULL_CORPUS_METRIC_EXECUTION.md).
Legacy subset runs are preserved but do not acquire missing observations.

Inspect `GET /openapi.json` for the route and `GET /metrics/catalog` for the
current database record counts. Each metric page reads saved records and offers
its corresponding calculator; the run report also links to these pages.
Controlled BSDA, recovery, and SAEA results will appear
there only after eligible real trajectories and measurements are executed and
persisted under their appropriate evidence class; this computation API does not
substitute for that process.

## Read-only stored metric evidence

`GET /metrics/compute/{metric}/evidence?limit=25&offset=0` projects saved
`scientific_records` into per-record measurements for the metric pages. It uses
the existing `/metrics/compute` proxy and existing API authentication; it does
not invoke models, recalculate a new estimator, write records or change run reports.
Recovery recognizes both `rc` and `recovery` families. Pagination is bounded
to 1–100 records and never averages unrelated runs.

Each response contains the actual record total, required evidence, source
identity/schema/status, allowlisted provenance, measured series with units,
and explicit per-point null/reason pairs. Failed/blocked/undefined records
do not become numeric pass results. Recovery raw deviations can be shown
without treating missing calibrated RC indices as zero. SAEA context effects
retain failed/control-missing gaps. DQI novelty/aggregate remain unavailable
without embeddings; DRAA/PRI charts show descriptive counts/coverage only.
ML/MCHL remain unavailable without eligible held-out labels/matched factual pairs.

`scientific_calibration` stays `not_established`: stored numbers, source counts,
caller-supplied calibration objects and engineering tests do not meet the
independent scientific criteria in the metric-specific specs. No scalar DRAA
risk, scalar PRI, ranking, synthetic UI observations or new decision thresholds
are introduced. The source-value table remains available alongside each chart.
