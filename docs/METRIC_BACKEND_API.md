# Metric computation API

The backend now exposes `GET /metrics/catalog`, `POST /metrics/compute/{metric}`
and `POST /metrics/compute/{metric}/save`.
The catalog reads current `scientific_records` counts and statuses; it does not
infer that a missing record has a numerical value. A signed-in workspace session
is required for computation when API authentication is enabled.

| Metric path | Existing source engine | Required POST body | Ordinary local run |
| --- | --- | --- | --- |
| `bsda` | `core.metrics.bsda.compute_bsda` | `value`: versioned `BSDAInput`; optional caller-supplied `calibration`, `semantic_adapter` (`lexical` or `none`) | Does not create matched baseline/perturbed responses |
| `recovery` | `RecoveryCapabilityEngine.evaluate_run` | `value`: `RecoveryRunInput`; optional `calibration` | Does not create baseline/attack/recovery state trajectories |
| `saea` | `SAEAEngine.evaluate` | `value`: `SAEAInput` with matched isolated controls and context status | Does not create sequential/isolated behavioral states |
| `draa` | `core.draa.diagnostics.summarize` | `records`: nonempty list of `DRAAEvidenceRecord` | Mode A evidence is computed and persisted per completed evaluation |
| `pri` | `core.pri.diagnostics.summarize` | `profile`: `PRIProfileRecord` | Mode A profile is computed and persisted per run |
| `dqi` | `core.dataset.quality.calculate_dqi` | `dataset`: `Dataset`; optional `embeddings` and `weights` | Repository example DQI is persisted; a new dataset needs its own calculation |
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

Inspect `GET /openapi.json` for the route and `GET /metrics/catalog` for the
current database record counts. Each metric page reads saved records and offers
its corresponding calculator; the run report also links to these pages.
Controlled BSDA, recovery, and SAEA results will appear
there only after eligible real trajectories and measurements are executed and
persisted under their appropriate evidence class; this computation API does not
substitute for that process.
