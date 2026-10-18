# Phase 10A statistical planning infrastructure

Phase 10A implements immutable, provider-neutral statistical planning and
provenance metadata in `core.statistics`. It does not perform statistical
inference. `ReadinessStates` separately records engineering, plan, data,
analysis, and claim-validation readiness; synthetic fixtures cannot establish
data readiness or a validated scientific claim.

## Phase 10B.1

Phase 10B.1 adds strict finite numeric validation, dependency-free descriptive
summaries (sample variance and inclusive linear-interpolated quartiles),
explicitly oriented raw/paired differences, and Pearson/Spearman coefficients.
Pair alignment and pairing declaration are required. Grouped/repeated data need
structured reduction provenance before ordinary correlation is allowed;
descriptive summaries remain explicitly descriptive. Semantic missingness stays
outside numeric arrays and is retained as omission provenance.

Plans preserve hypotheses (including estimation-only hypotheses without H0/H1),
estimands, optional analysis hierarchy, grouping, explicit pairing, resampling,
multiplicity, effect-size, missingness, and assumption metadata. These plans
hold configurable choices without silently supplying alpha, confidence level,
bootstrap count, BCa, effect threshold, or missingness mechanism.

The method registry contains metadata for future descriptive, correlation,
test, ANOVA, regression, mixed-model, and bootstrap families. It does not
select or execute methods. Mixed-model entries are honestly dependency-gated.
Preregistration metadata supports draft/frozen/amended/superseded plans without
external-service integration.

Component guards preserve BSDA components rather than composites, require RC
calibration provenance for a degradation threshold, preserve SAEA CV_obs and
non-causal Shapley semantics, reject DRAA Mode A/B risk validation and PRI
scalar/ranking validation, reject synthetic Phase 9B prediction claims and
same-judge Layer 2 reference labels, and flag provenance-visible DQI circularity.

`StatisticalExperimentArtifact` is metadata only. `StatisticalResultRecord`
defaults to `not_computed` and all numerical inference fields remain null.
Deterministic JSON serialization retains enums, provenance, null values, and a
stable plan hash. Run `python -m scripts.statistics_smoke` to verify a metadata
only BSDA planning example.

## What Phase 10A Does Not Yet Establish

- no statistical validation has been run;
- no p-values, confidence intervals, bootstrap, t-tests, rank tests, ANOVA,
  regression, mixed models, multiplicity adjustment, component validation, or
  model ranking from Phase 10B.1;
- no p-values, confidence intervals, bootstrap, or effect sizes are computed;
- no model comparisons, BSDA, RC, SAEA, or Layer 2 agreement claim;
- no DRAA risk, PRI scalar, or ML predictive validation; and
- no universal scientific threshold.
