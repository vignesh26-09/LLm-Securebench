# PRI Mode A/B implementation

PRI Mode A/B is implemented as provider-neutral **profile infrastructure**, not a robustness estimator. `PRIProfileRecord` represents one declared evaluated system configuration over one benchmark population. It is always `UNCALIBRATED` and has `scalar_pri = null`.

## Profile-first architecture

The record preserves actual model/provider/version and available generation, seed, system/developer/harness, policy/taxonomy metadata without inventing absent values. It also retains benchmark/dataset/version/hash, threat model, requested/observed categories, run IDs, provenance, warnings, and errors.

Evidence is a lossless two-axis cell: declared benchmark category plus an optional explicitly supplied construct, source namespace/feature, source-native value/units/orientation, status/reason, upstream uncertainty/confidence, hierarchy IDs, and provenance. No category-to-construct mapping is inferred.

Partial profiles are valid only with explicit requested/observed categories, category statuses, hierarchy counts, and cell status counts. Missing categories are never converted to zero or renormalized.

## Upstream integration

PRI can receive original artifacts as cells or use DRAA Mode A/B evidence as transport. DRAA remains uncalibrated and no risk score is consumed. Layer 1/2, BSDA components, RC payloads, and heterogeneous SAEA artifacts retain their existing meanings. Duplicate provenance between direct and DRAA evidence is warned about rather than double-counted.

Mode B offers only coverage/status/source/hierarchy/uncertainty counts and source-labelled numeric descriptions. Compatibility compares explicit benchmark, taxonomy, threat-model, policy, system-context, and harness metadata as `compatible`, `incompatible`, or `unknown`; it does not rank models or use tolerance rules.

`PRIReferenceArtifact` is a future schema only for methodology, reference population, estimators, normalization, policies, and validation provenance. It does not fit or apply a model.

## What PRI Does Not Yet Do

- no validated category estimators;
- no scalar PRI, category weights, macro/micro aggregation, or model ranking;
- no normalization or reference-model population;
- no hierarchical inferential CI;
- no cross-robustness score;
- no ICC/JSD, survival, breach-frequency, RC-transition, or sequential-hazard estimator.

PRI Mode A/B implementation is infrastructure, not scientific validation of PRI.
