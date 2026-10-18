# Phase 10B basic statistical methods formal specification

## 1. Purpose

Define a small, dependency-light numerical utility layer. It computes declared
quantities only and never validates a scientific claim.

## 2. Scope boundary

Allowed: descriptive summaries, explicit raw/paired differences, Pearson and
Spearman coefficients, paired/Welch test statistics, Mann-Whitney/Wilcoxon
rank statistics, basic effect sizes, and simple bootstrap metadata/utilities.
All regression, ANOVA, mixed/cluster/hierarchical methods, permutation,
multiplicity, power, calibration, and component runners are deferred.

## 3. Relationship to Phase 10A

Phase 10A supplies plan, pairing, grouping, missingness, assumption, readiness,
and provenance contracts. Phase 10B must accept or attach these contracts; it
must not infer readiness or set `claim_validated`.

## 4. Numerical result-status model

Each result has one computation status: `computed`, `not_computed`,
`undefined`, `insufficient_data`, `invalid_input`, `not_applicable`, or
`numerical_failure`. It separately preserves Phase 10A assumption status,
warnings, diagnostics, omission counts, and provenance. `assumption_unassessed`
or `assumption_violated` belongs in assumption metadata, not the numerical
status unless the caller configures a plan-level block.

## 5. Numeric input policy

Accept finite `int` and `float`, excluding `bool`. Reject strings, categories,
ordinals without caller-provided numeric encoding, `None`, NaN, and infinities.
Utilities receive already-filtered observations or an explicit omission policy;
they never coerce any value to zero. Paired/correlation inputs preserve aligned
omitted-pair counts.

## 6. Missingness handling

Semantic statuses are not observations. The caller/Phase 10A plan chooses which
states are included; a Phase 10B result reports original, valid, missing, and
excluded-by-status counts/reasons. It neither removes a status by default nor
assigns MCAR/MAR/MNAR meaning.

## 7. Clustering guard

Basic methods are not cluster-aware. If plan grouping declares repeated/nested
or unresolved dependence, ordinary methods must return `not_applicable` unless
the caller provides an explicit acknowledgement that input was reduced to
independent declared units. A warning-only override is insufficient.

## 8. Pairing guard

Pairing is explicit keys or an explicit positional-pairing option. A paired
plan rejects Welch/Mann-Whitney; an unpaired/unknown plan rejects paired
t/Wilcoxon. Incomplete pairs are reported and dropped only when caller policy
explicitly permits complete-case paired analysis.

## 9. Descriptive statistics

For finite observations report total/valid/omitted counts, min/max, arithmetic
mean, median, sample variance/SD (`n-1`), and optional quartiles/IQR using the
documented inclusive linear-interpolation quantile convention. `n=0` is
insufficient; `n=1` has mean/median/min/max but sample variance/SD undefined;
constant vectors have variance/SD zero. No CI is implied.

## 10. Raw differences

`difference(x, y, orientation)` computes scalar or aligned-vector `x-y` or
`y-x`; orientation is required. Vectors require equal aligned length. Invalid
or omitted entries are not silently paired; output preserves omitted indices.

## 11. Paired differences

Complete matched pairs yield ordered raw differences and count, mean/median,
and sample SD where defined. Positional alignment is permitted only by explicit
API choice. Identical pairs yield valid zero differences; standardization may
be undefined with zero SD.

## 12. Pearson correlation

For `n>=2`, compute `r=sum((x-xbar)(y-ybar))/sqrt(sum(dx²)sum(dy²))` using
stable two-pass centered sums. Constant variables produce `undefined`; bounds
are [-1,1], with only tolerance-limited rounding to a theoretical bound
clamped. Return coefficient only, never causal/inferential interpretation.

## 13. Spearman correlation

Compute Pearson correlation of average ranks. Ties receive average ranks; the
no-ties shortcut is prohibited. Require `n>=2` and nonconstant rank vectors.
Return rho only; no universal magnitude interpretation.

## 14. Paired t-test

From complete differences, require `n>=2`: `t=dbar/(sd/sqrt(n))`, df=`n-1`.
Alternative is an explicit `two_sided`, `greater`, or `less` label. All-zero
differences give undefined statistic; nonzero constant differences give
undefined/infinite-limit behavior and must be reported `undefined` with
diagnostic rather than fabricated infinity. No normality test is run.

## 15. Welch t-test

For independent finite groups, require at least two observations per group.
Compute `t=(mean_x-mean_y)/sqrt(sx²/nx+sy²/ny)` and Welch-Satterthwaite df.
One zero variance group is valid if denominator is positive; both equal constant
groups are undefined, and unequal constant groups are undefined/infinite-limit.
Pooled Student t is excluded.

## 16. Mann-Whitney U

Independent groups only. Rank pooled observations with average ties;
`U1=R1-n1(n1+1)/2`, `U2=n1*n2-U1`; report `U1` with orientation plus both
values. Require one observation in each group. It describes rank/stochastic
ordering under appropriate assumptions, not a generic median test. No p-value.

## 17. Wilcoxon signed-rank

Paired observations only. Phase 10B uses one explicit convention: discard zero
differences, report discarded-zero count, rank absolute nonzero differences
with average ties, and report `W+`, `W-`, and `min(W+,W-)`. Require at least one
nonzero pair; all-zero data are undefined. It is not unconditionally a median
test. No exact/asymptotic p-value.

## 18. P-value strategy

No p-values in initial Phase 10B. Exact CDF/tie corrections and reliable t
distribution tails require an approved numerical backend; hand-written
distribution approximations are rejected. Results preserve `p_value=None` and
backend-unavailable/not-computed metadata. Optional future SciPy integration is
separately specified and cannot change effect/statistic meaning.

## 19. Effect-size framework

Return source-native raw mean difference, paired mean difference, independent
Cliff delta, Mann-Whitney rank-biserial, Wilcoxon rank-biserial, and Pearson/
Spearman association coefficients. Every result records orientation, design,
denominator where applicable, and undefined reason. No magnitude labels.

## 20. Hedges g decision

Defer Hedges g. Independent and paired variants have distinct denominators and
small-sample conventions; Phase 10A has not approved one. Do not substitute a
paired formulation for independent Hedges g.

## 21. Rank-biserial correlation

For Mann-Whitney use `(U1-U2)/(n1*n2)` with group-one orientation. For Wilcoxon
use `(W+-W-)/(W++W-)` after the declared zero policy. Both are undefined when
their denominator is zero and must not share an undocumented formula.

## 22. Cliff's delta

For independent groups compute `(count(x>y)-count(x<y))/(n_x*n_y)`, ties zero,
with first-group orientation. An O(n*m) implementation is acceptable for the
small Phase 10B surface; optimize only after profiling. All ties return zero.

## 23. Simple bootstrap scope

Optional 10B.4 supports only IID bootstrap for caller-acknowledged independent
units and paired bootstrap resampling complete pairs together. Require callback
or approved statistic identifier, explicit B, explicit confidence level, and
optional seed. Percentile interval only. No hierarchical/BCa bootstrap.

## 24. Percentile interval contract

For confidence `c`, use sorted valid replicate statistics and linear-interpolated
quantiles at `(1-c)/2` and `1-(1-c)/2`; endpoints are included as returned
values. Preserve method, requested/valid resamples, confidence, seed, callback
identity, status, and warnings. It is not universally valid.

## 25. Bootstrap failure handling

Invalid B/confidence or empty input is invalid/insufficient. Constant input is
valid if the callback is defined. Undefined replicate statistics are counted
and omitted only under caller-declared failure policy; absent such a policy any
undefined replicate makes result not computed. All undefined is undefined.
Callback type changes/non-finite output are invalid/numerical failure.

## 26. Numerical stability

Use finite checks, stable/two-pass variance, centered products, and average-tie
ranks. Do not add arbitrary precision. Large or tiny finite values that overflow
intermediate calculations yield numerical failure, never a silent clamp.

## 27. Floating-point policy

Exact equality is valid for documented input equality and ties. Use an explicit
engineering epsilon only to repair a theoretically bounded correlation within
rounding distance of ±1; do not use tolerance to erase nonzero variance or
differences. Tiny negative variance from rounding is repaired only when within
documented machine-scale tolerance, otherwise numerical failure.

## 28. Result schema

Extend `StatisticalResultRecord` with computation status, n_total/n_valid/
missing_count/dropped_pair_count, estimate/statistic/df/alternative/effect
mapping/interval, p-value nullable, warnings, numerical notes, assumption
status, backend, and provenance. No field derives a scientific verdict.

## 29. Assumption metadata

Use Phase 10A `AssumptionRecord`; do not auto-test or switch methods. Paired t
records pairing/independent-pair/suitable-difference assumptions; Welch records
independent groups; rank methods record their interpretation constraints; Pearson
and Spearman record association and ordinary-inference independence assumptions.

## 30. Multiplicity boundary

No adjustment is implemented. Future p-value results may carry family metadata
but cannot apply Holm/BH/Bonferroni in Phase 10B.

## 31. Component boundary

Utilities are generic. No `validate_bsda`, `validate_rc`, `validate_saea`, DRAA
risk, PRI, ranking, or ML validation function is allowed.

## 32. Dependency policy

Do not add SciPy now. Implement descriptive/statistic/effect calculations with
the standard library; defer CDF-dependent p-values. A future optional SciPy
backend can be capability-gated without becoming a required dependency.

## 33. Reference compatibility

When native methods are implemented, optional developer tests may compare their
statistics with SciPy if installed. Tolerances are engineering parameters and
tests skip when SciPy is absent.

## 34. Edge-case test matrix

Test empty/one/constant/normal/large/non-finite descriptives; complete,
unmatched, reversed, identical paired data; perfect/constant/short/missing
Pearson and tied/constant/short Spearman; hand-calculated, zero-variance, and
alternatives for t tests; disjoint/equal/tied/tiny and pairing rejection for U;
positive/negative/zero/tied/independent rejection for Wilcoxon; effect sign,
zero variance, dominance/ties; deterministic/invalid/constant/partial-failure
IID and paired bootstrap; and null/status/provenance serialization.

## 35. Scientific claim restrictions

A p-value or CI never validates a claim; correlation is not construct validity;
Mann-Whitney/Wilcoxon do not automatically prove median shifts; t tests do not
solve clustering; bootstrap validity follows its design. No utility sets
`claim_validated`.

## 36. Staged implementation recommendation

10B.1: statuses, numeric filtering, descriptives, raw/paired differences,
Pearson/Spearman, schemas. 10B.2: paired/Welch statistics and safe effects.
10B.3: rank tests. 10B.4: optional IID/paired percentile bootstrap. 10B.5:
optional approved p-value backend. This is appropriate and intentionally narrow.

## 37. Implementation-ready methods

Without dependencies: all 10B.1 computations, paired/Welch statistic and df,
raw/paired differences, rank statistics, rank-biserial, Cliff delta, and
standard-library IID/paired bootstrap after explicit plan configuration.

## 38. Deferred methods

P-values, Hedges g, BCa/hierarchical bootstrap, permutation, ANOVA, regression,
mixed/cluster methods, multiplicity, power, calibration, and component runners.

## 39. Blockers

Blocked choices include a universal alpha/CI/B/effect threshold, real data
independence design, RC degradation threshold, DRAA risk, PRI scalar, and a
reliable distribution backend without dependency approval.

## 40. Exact recommended Codex scope

Implement 10B.1 first: dependency-free finite numeric validation, explicit
result statuses, descriptive/paired difference utilities, Pearson/Spearman
coefficients, Phase 10A clustering/pairing/missingness guards, and deterministic
serialization. Do not implement p-values or bootstrap in that first slice.

### Direct answers

1. No SciPy now. 2–4. No first-slice or correlation p-values. 5–6. Paired and
Welch return t/df only. 7–8. No exact rank-test p-values. 9. Wilcoxon discards
zeros. 10. No Hedges g initially. 11. Raw/paired differences, correlations,
rank-biserial, Cliff delta. 12–13. Bootstrap later, IID/paired percentile only.
14. No BCa. 15. Hard-block unresolved clustering absent acknowledgement. 16.
Pairing mismatch is not applicable. 17. Preserve caller-declared semantic
omissions/counts. 18. Section 37 methods. 19. Section 38 methods. 20. 10B.1.
