# Additive evidence layers

SecureLLMBench records four additive research-software artifacts without changing the meanings of BSDA, Recovery Capability, SAEA, ASR, DRAA, PRI, or DQI.

- **Canary evidence** records an injected request marker, provider verification evidence, and an explicit status. Canary verification is probabilistic, request-level evidence rather than proof that a provider retained all prior context. A reported canary failure blocks RC and SAEA input by producing a truncated context gate. Missing provider evidence remains `canary_undetermined`; it is not a successful verification.
- **Preregistration** is immutable once locked. A correction creates a new, linked version and requires an amendment reason. Analysis-plan comparisons label items either `as_planned` or `exploratory_not_preregistered`.
- **Contamination ledger** records the identifiers and provider metadata used for every isolated-vs-sequential comparison. A shared conversation ID is `isolation_suspected_leak` and blocks the isolated SAEA delta. Missing cache-isolation evidence is `isolation_unverifiable`, not verification.
- **Replication bundle** exports the specification, exact stored conversation messages, observations, manifest, preregistration artifacts, contamination records, and optionally supplied Layer 1/Layer 2 signals. Replay reports factual response, signal, and context differences without asserting reproducibility from a single match.

Persisted artifacts can be exposed through the read-only API at `GET /research-evidence/{family}` for `preregistration`, `analysis_plan_diff`, `session_contamination`, `replication_bundle`, `replication_replay`, and `reproducibility_manifest`. The existing append-only scientific-record adapter rejects a second artifact with the same ID.

These records support traceability and explicit blocking. They do **not** validate a judge, establish human-label agreement, prove model safety, establish causal effects, provide statistical significance, or justify a model-selection recommendation.

Publication-chart eligibility is separate from operational persistence. A record must explicitly declare `data_origin: real_persisted` and a reporting class of either `phase1_scientific` or `external_calibration`; engineering-only records are never eligible by omission or by a generic real-data label.
