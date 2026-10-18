# PRI Methodology-to-Implementation Reconciliation

**Status:** Documentation-only Phase 8.5 reconciliation. PRI application code is not authorized here.

This reviews `D:\PRI_FORMAL_SPEC.md` against actual SecureLLMBench contracts. PRI must preserve upstream meanings, applicability, uncertainty, and provenance; it must not retrofit new semantics into Layer 1/2, BSDA, RC, SAEA, or DRAA.

## 1. Authoritative PRI role

PRI is model/configuration-level assessment over a declared benchmark population. Its defensible primary output is a profile of separate, provenance-preserving category/construct evidence. It is distinct from BSDA case behavioral change, RC recovery, SAEA sequential effects, and DRAA uncalibrated case/session evidence transport.

**FORMALLY DEFINED.**

## 2. Evaluated system unit

The proposed configuration is `(model/version, generation settings, system/developer context, harness/tooling, policy/taxonomy version)`. Current runtime fields support model name/provider/version, optional context window/metadata, generation temperature/token/time limits, benchmark run ID, seed where supplied, and source metadata. They do not mandate system/developer/harness/policy identifiers.

Comparability requires preservation of all supplied model/provider/version, generation configuration, seed, dataset/version/hash, taxonomy/policy, system/developer/harness, and scoring prompt/rubric/provider versions. Absence must be explicit. Dataset/taxonomy/policy mismatches invalidate direct comparison. A harness change identifies a different evaluated configuration. A bounded-generation-equivalence rule is absent.

**FORMALLY DEFINED** for provenance preservation; **IMPLEMENTATION DEFAULT** for explicit absence; **BLOCKER** for generation-range equivalence.

## 3. PRI versus DRAA

DRAA Mode A/B is optional PRI evidence transport. PRI may instead consume original upstream artifacts. DRAA is `UNCALIBRATED` with `risk_score = None`; PRI must never depend on a DRAA scalar or aggregate DRAA output again.

**FORMALLY DEFINED.**

## 4. Category axis versus robustness-construct axis

The proposal gives non-equivalent axes: categories (injection, leakage, jailbreak, semantic drift, recovery, sequential) and constructs (attack resistance, stability, safety preservation, leakage resistance, instruction integrity, recovery, sequential resilience, cross-robustness). No mapping is established: injection can concern several constructs, while recovery is trajectory conditional.

A safe Mode A record may use a two-axis evidence table (`benchmark_category × observed construct/source`) without claiming each cell has a common estimator. Neither axis may be collapsed or missing cells filled.

**BLOCKER** for a canonical PRI profile schema; **IMPLEMENTATION DEFAULT** for two-axis evidence storage.

## 5. Upstream contracts

| Source | Actual contract and permitted PRI role |
| --- | --- |
| Layer 1 | Detector-native score/confidence/evidence/signal/metadata; not binary truth or an automatic filter. Preserve as case evidence. |
| Layer 2 | Dimension-specific score/label/confidence/applicability/uncertainty and provider/model/prompt/rubric versions; a measurement, not calibrated probability or ground truth. |
| BSDA | Semantic, safety, instruction, structural component vector with raw/optional normalized values, CI, and unmeasurability. No composite. |
| RC | Documented `RC_AUC_raw`, bounded display value, terminal recovery, and explicit applicability/calibration states. No typed runtime result exists. |
| SAEA | Δ trajectory, isolated controls, context effects, `CV_obs`, candidate SI, order/Shapley/RC-trend outputs. SI may be undefined; no composite. |
| DRAA | Optional uncalibrated evidence/provenance transport. |

**FORMALLY DEFINED.**

## 6. Candidate category estimators

| Proposed estimator | Reconciliation |
| --- | --- |
| Injection robustness | No target unaligned-state label/estimator exists; Layer 1/2/BSDA are evidence only. **BLOCKER.** |
| Leakage frequency/severity | No breach definition, severity taxonomy, or repeated labelled design. **BLOCKER.** |
| Jailbreak survival probability | Needs escalation protocol, unbroken label, budget, censoring, and sampling unit. **EMPIRICAL HYPOTHESIS / BLOCKER.** |
| Semantic drift ICC/JSD | BSDA does not compute ICC/JSD; it has four approved components. **BLOCKER:** new methodology, not a BSDA replacement. |
| Recovery transition rate | RC is trajectory recovery after measurable degradation, not `P(compliant T+1 | violated T)`. Actual RC outputs are diagnostic evidence only. **BLOCKER** for proposed rate. |
| Sequential hazard | SAEA is neither hazard nor autocorrelation model. Preserve actual `CV_obs`, SI, context/order/Shapley/RC-trend outputs. **BLOCKER** for hazard. |

Every rate/probability needs a label policy, applicability, repeated-observation design, sampling unit, uncertainty, and missingness policy; none is specified.

## 7. Benchmark population

PRI is benchmark-distribution-dependent. Every result must identify whether it is benchmark-specific, threat-model-specific, or relative to a versioned standardized reference distribution. Cross-benchmark comparison needs compatible benchmark/taxonomy/reference contracts. Standard-core and threat-specific population concepts are study designs, but their sampling/weighting is undefined.

**FORMALLY DEFINED** for distribution dependence; **CALIBRATION-DEPENDENT** for reference populations; **BLOCKER** for standardized cross-benchmark profiles.

## 8. Hierarchical sampling structure

Intended hierarchy: configuration → category → attack family → base case → prompt variant → stochastic generation → optional session/sequence. Existing records identify run/evaluation/case/record; SAEA adds sequence/instance/position; datasets may contain metadata but do not mandate all hierarchy IDs.

Safe aggregation retains every available hierarchy ID and counts unique units. Repeated generations are repeated outcomes, not automatically independent cases. Sessions/sequences and member attacks remain clustered. A versioned family/case/variant taxonomy is required for inference.

**IMPLEMENTATION DEFAULT** for hierarchy-preserving storage; **BLOCKER** for independence assumptions.

## 9. Stochastic-run handling

Mode A retains seeds/configuration, run count, observations, and failures. Mode B may report counts, distributions, mean/median, variance, quantiles, and observed status proportions only with an explicit quantity and grouping. These are descriptive, not robustness probabilities absent an approved estimand.

**IMPLEMENTATION DEFAULT** for storage; **EMPIRICAL HYPOTHESIS** for inference.

## 10. Aggregation: macro, micro, and cross-category

Macro equally weights categories; micro weights items. Both are distributional weighting choices. The profile-first PRI formal spec provides no approved category weights, common estimand, or scalar `psi`. Category-level results can remain separate only after their individual estimator is approved.

Cross-category means, weighted means, and `0.5*A + 0.5*B` scalars are prohibited.

**BLOCKER. Scalar PRI is not implementation-ready.**

## 11. Normalization

Do not force values into `[0,1]`. Layer 1 is detector-native; Layer 2 orientation is rubric-dependent; BSDA has raw/optional artifact-normalized components; RC raw can be negative/undefined; SAEA fields differ in unit and condition. Reference, anchor-model, percentile, and min/max transforms need versioned reference data and compatibility policy. No anchors/minimums exist.

**BLOCKER** for profile comparison/scalarization; **CALIBRATION-DEPENDENT** for later transformation.

## 12. Missingness and applicability

Distinguish not evaluated, not applicable, failed, insufficient data, undefined, unavailable upstream, uncalibrated, and incompatible benchmark version. Partial profiles are permitted only as coverage-bearing evidence tables with requested/observed category-construct cells, hierarchy coverage, source/status counts, and each absence reason. Never renormalize over available cells.

**FORMALLY DEFINED** for preservation; **BLOCKER** for partial-profile comparison/ranking.

## 13. Uncertainty

Retain upstream uncertainty with source meaning. A 95% IID bootstrap is not automatically valid: resampling may need family, case, or hierarchical/session clusters. Cluster/hierarchical bootstrap, mixed-effects, and Bayesian hierarchy are future candidates after an estimand/taxonomy exists. Confidence level, replicates, method, and resampling unit are unresolved.

**BLOCKER** for PRI inferential uncertainty; **IMPLEMENTATION DEFAULT** for upstream uncertainty preservation.

## 14. Cross-robustness and weakest-category diagnostics

Category Cross-Robustness has no estimator. Dispersion/entropy/minimum/variance would be new methodology. A weakest-category listing is only a descriptive diagnostic when outputs share approved scale, direction, population, and coverage; otherwise show values without ordering.

**DIAGNOSTIC** where compatible; otherwise **BLOCKER**.

## 15. Model comparability and ranking

Do not rank incompatible benchmarks, taxonomies, policies, harnesses, partial profiles without qualification, or uncalibrated heterogeneous scalarizations. Tiny differences need uncertainty and rank stability. Future work needs paired/cluster-aware uncertainty, family/dataset sensitivity, category-weight/normalization sensitivity, and distribution-shift analysis.

**BLOCKER** for current ranking; **FUTURE WORK** for ranked comparisons.

## 16. Reference/calibration artifact

A future immutable `PRIReferenceArtifact` requires PRI methodology; benchmark hash; taxonomy/threat/category definitions; estimators; configuration requirements; reference population; normalization; any approved weighting; missingness/stochastic/hierarchy/resampling policy; uncertainty method; validation status; seeds/timestamps/provenance. No implicit default may populate it.

**CALIBRATION-DEPENDENT.**

## 17. Safe implementation modes

| Mode | Permitted function | Status |
| --- | --- | --- |
| A | Model-level evidence/profile assembly by explicit configuration, category, and available hierarchy. | IMPLEMENTATION-READY |
| B | Coverage, run/family/case/variant counts, missingness, distributions, profile completeness, compatibility checks. | IMPLEMENTATION-READY |
| C | Validated category estimators with labels, estimands, sampling, and uncertainty. | BLOCKER |
| D | Scalar PRI with cross-category estimand, weighting/reference, normalization, uncertainty, validation. | BLOCKER |

This staged approach prevents DRAA-style case aggregation and is appropriate.

## 18. Validation plan

Future validation: repeated benchmark runs; between-model discrimination; attack-family/dataset/model-family holdouts; category-removal and weighting sensitivity; duplicate/easy-case sensitivity; simple attack-success/category-summary/expert-assessment comparisons; rank stability; uncertainty coverage; and benchmark-distribution shift. Prevent leakage across related family/case/variant/session observations. No universal sample size/performance threshold is established.

**FUTURE WORK / EMPIRICAL HYPOTHESIS.**

## 19. Resolved decisions

| Decision | Reconciliation | Classification |
| --- | --- | --- |
| Scope | Configuration/profile level over declared population. | FORMALLY DEFINED |
| Primary result | Profile/evidence, not scalar PRI. | FORMALLY DEFINED |
| DRAA | Optional evidence transport, never scalar input. | FORMALLY DEFINED |
| Layer 1/2 | Actual scores/statuses, not binary truth/probabilities. | FORMALLY DEFINED |
| BSDA | Four components; no JSD/ICC substitution/composite. | FORMALLY DEFINED |
| RC | Actual trajectory results only; no conditional-rate replacement. | FORMALLY DEFINED |
| SAEA | Heterogeneous outputs; no hazard/autocorrelation replacement. | FORMALLY DEFINED |
| Partial results | Allowed with explicit coverage/status metadata. | IMPLEMENTATION DEFAULT |

## 20. Implementation blockers

1. Canonical profile axis: categories, constructs, or approved two-axis cells.
2. Category estimators and labels for all six proposed categories.
3. Macro/micro/cross-category estimand, scalar function, and weights.
4. Shared scale/direction/reference normalization.
5. Hierarchical independence/resampling and uncertainty procedure.
6. Cross-robustness estimator and partial-profile comparison/ranking policy.
7. Typed RC runtime result contract, currently absent.

## 21. Recommended next step

**PRI profile infrastructure is implementation-ready; scalar PRI is not implementation-ready.**

The safe next engineering scope is Mode A/B profile assembly that stores configuration identity, benchmark/taxonomy coverage, hierarchy, upstream artifacts, statuses, and descriptive diagnostics without estimating category robustness or ranking models. In parallel, preregister category estimands, labels, benchmark population, and hierarchical uncertainty protocol before Mode C/D work.
