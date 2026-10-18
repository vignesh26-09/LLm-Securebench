# Statistical validation implementation reconciliation

## 1. Authoritative Phase 10 role

Phase 10 establishes an implementation-safe contract for planning, recording,
and eventually reproducing statistical studies. It does not itself validate a
component or scientific claim. The current `core.statistics` package contains
only a `StatisticalAnalyzer` protocol; no statistical analysis runtime exists.

The required distinction is: **ENGINEERING_READY** means infrastructure can be
implemented; **PLAN_READY** means an estimand and protocol are sufficiently
specified; **DATA_READY** means appropriate data and provenance exist;
**ANALYSIS_READY** means the selected design assumptions and inputs have been
checked; **CLAIM_VALIDATED** requires completed, appropriate empirical work and
scientific review. These are separate states, never one boolean.

## 2. Upstream contract corrections

DQI is exploratory and unvalidated. Its implemented components are duplicate
quality, prompt coverage, category entropy, embedding-dependent novelty,
difficulty entropy, and category balance; the existing weighted formula must
not change and must not be validated against quantities derived from itself.

Layer 1 is heuristic detector-native evidence, not truth. Layer 2 is a
dimension-specific judge measurement with applicability, status, confidence,
uncertainty, and provenance; neither its score nor confidence is automatically
a probability. BSDA remains the independent semantic, safety, instruction, and
structural component vector with no composite.

RC has an approved specification but no runtime implementation. It means
recovery after degradation, preserving raw/bounded RC-AUC where applicable,
terminal recovery, calibration-artifact applicability, and context-truncation
concerns. SAEA retains its trajectory, isolated controls, context effects,
`CV_obs` cumulative vulnerability, candidate Bliss-style SI, order effects,
Shapley attribution, and recovery trends. SI may be undefined. Neither metric
receives a new estimator here.

DRAA Mode A/B is evidence transport/descriptive diagnostics with
`risk_score = None`; only fidelity, completeness, provenance, missingness, and
reproducibility can be studied. PRI Mode A/B is profile infrastructure with
`scalar_pri = None`; category estimators and ranking remain unresolved. Phase
9A/B ML is engineering-only and does not establish prediction without
independent labels and real held-out evaluation.

## 3. Rejected arbitrary thresholds

The following Gemini values are rejected as project-wide defaults or validity
gates: Krippendorff alpha 0.80; kappa cutoffs; ECE 0.05; BSS 0.10; ROC-AUC
0.80; Kendall tau 0.85/0.90; correlation 0.70 or 0.20; Hedges g 1.0/0.2;
alpha 0.01/0.05; p < .001; power 0.80; 30 pairs; VIF 5; bootstrap counts
2,000/10,000; five seeds; three paraphrases; +/-50% weights; <20% degradation;
fixed temperatures, equivalence margins, perturbation percentages, and fixed
confidence levels.

Each may be an **IMPLEMENTATION EXAMPLE**, **PREREGISTRATION PARAMETER**,
**CALIBRATION-DEPENDENT** value, **EMPIRICAL HYPOTHESIS**, **FUTURE WORK**, or
a **BLOCKER**, depending on the study. None is a validated SecureLLMBench
threshold. Scientific parameters should be required fields in a future plan,
with no implicit default.

## 4. Scientific readiness states

Plans must store all five readiness states from Section 1 separately. A plan
can be engineering- and plan-ready while data are absent. A completed method
can be analysis-ready without validating its claim. Synthetic studies exercise
software and protocol handling only; they do not become data-ready scientific
validation.

## 5. Claim/estimand architecture

Every future hypothesis must name the component/construct, target population,
estimand, comparison, effect scale, inclusion/exclusion rules, and claim scope.
An estimand is not a metric name or a generic “validation score.” It must also
identify whether the claim is descriptive, reliability, agreement, criterion,
construct, calibration, sensitivity, or generalization related.

## 6. Experimental units

An analysis plan must identify experimental unit, sampling/resampling unit,
and observation record separately. Candidate units include model configuration,
dataset/benchmark, category, attack family, base case, prompt variant,
stochastic run, session/sequence, and turn—but all are optional because current
dataset and benchmark contracts do not guarantee them.

## 7. Hierarchy/grouping

Grouping fields must be preserved when actually supplied, with missing IDs
remaining missing. The plan names the grouping hierarchy and its role (design,
pairing, resampling, or model term). It must not fabricate a random effect or
assume repeated generations are independent cases.

## 8. Pairing

Pairing must be declared, not inferred from proximity. Typical paired designs
include baseline/attacked BSDA responses, isolated/sequential SAEA controls,
same prompt across models, and attack/recovery trajectories. Pairing informs
candidate methods but does not automatically select one.

## 9. Pseudoreplication controls

The plan must state how repeated prompts, variants, runs, turns, sequences, or
shared attacks are clustered. It should retain a parent unit and require the
same configured parent to remain together in grouped splitting/resampling.
Whether repeated runs represent independent sessions is an explicit design
assumption, not an ID convention.

## 10. Statistical method registry

A future registry may describe candidate descriptive summaries, Pearson and
rank correlations, paired/Welch tests, Wilcoxon, Mann-Whitney, permutation,
ANOVA, regression, mixed models, ordinal models, and resampling. Each entry
must record intended estimand, design requirements, assumptions, pairing and
grouping requirements, output semantics, and applicability status. It must not
be an automatic normality-to-test decision tree.

## 11. Correlation methods

Pearson describes linear association; Spearman describes monotonic rank
association; Kendall tau is another rank association. Assumptions for inference
are distinct from the definitions of these coefficients. Clustering and repeated
measures can make ordinary correlations misleading, and magnitude cutoffs are
not universal. Repeated-measures methods or regression/mixed models may be
better depending on the estimand.

## 12. t-tests

Paired t-tests concern paired differences; Welch tests concern independent
groups without assuming equal variance. A 30-observation CLT rule is rejected.
Choice depends on the sampled structure, difference distribution, influence,
outliers, and inferential objective—not merely a pretest.

## 13. Rank/non-parametric tests

Mann-Whitney requires independent groups; Wilcoxon signed-rank requires paired
data and assumptions about its difference distribution. Permutation or paired
bootstrap approaches may be appropriate under an exchangeability/design
argument. No non-parametric test is an automatic fallback.

## 14. ANOVA

Classical ANOVA remains available for simple, appropriate designs. Repeated or
hierarchical observations may instead require a repeated-measures, mixed, or
other strategy. ANOVA is neither universally invalid nor universally preferred.

## 15. Regression/mixed models

Mixed-effects/GLMM capability is important future infrastructure for genuinely
hierarchical data, but it is not mandatory for every estimand. Random-effect
structure must follow the sampling design; arbitrary available IDs are not
automatically random effects, and sparse clusters can make complex models
unstable. Future implementation would likely require an explicitly approved
dependency such as `statsmodels`; none is required now.

## 16. Cluster-robust inference

Mixed models, cluster-robust covariance, generalized estimating equations, and
grouped bootstrap are distinct approaches that may be alternatives or
complements. Cluster-robust SE is not mandatory with every mixed model. A plan
must record its inference strategy and why it preserves relevant dependence.

## 17. Permutation/randomization

Randomization/permutation tests are future candidate methods when an explicit
exchangeability or randomization design supports them. Their shuffle unit must
respect declared pairing/grouping. No universally valid permutation mechanism
or resample count is defined here.

## 18. Confidence intervals

Intervals are scientifically appropriate for inferential claims when their
method and assumptions match the design; they need not accompany every
descriptive statistic. Analytical, model-based, cluster-robust, grouped,
hierarchical, paired-bootstrap, percentile, BCa, and future Bayesian intervals
are analysis-specific options. A 95% interval is not mandatory.

## 19. Bootstrap/resampling

Resampling must preserve dependence: BSDA resamples base cases with matched
conditions, RC resamples complete sessions/trajectories, SAEA resamples suitable
sessions/sequences/family clusters while retaining order, Layer 2 resamples
complete judge/human cases, and ML resamples held-out groups as appropriate.
BCa is not mandatory. Method, confidence level, seed, and count are
preregistered/configurable; B >= 2,000 or 10,000 is not hard-coded.

## 20. Effect sizes

Future plans may define raw paired difference, standardized mean difference,
Hedges g, rank-biserial, Cliff delta, risk/odds ratio, regression coefficient,
marginal effect, partial R², Brier skill score, AUC difference, or correlation.
Raw-scale effects are preferred when interpretable. No effect is mandated by
sample size, and no effect-size cutoff establishes practical significance.

## 21. Multiplicity

Hypothesis families and the error-rate goal must be declared. Holm,
Bonferroni, Benjamini-Hochberg, hierarchical testing, and preregistered primary
outcomes are candidate strategies. There is no fixed alpha/FDR, no permanent
“Holm for family A”/“BH for family B” rule, and exploratory adjusted/unadjusted
outputs must be labelled as such.

## 22. Sample-size/power

Planning considers estimand, smallest relevant effect or precision target,
variance, dependence/ICC, prevalence, attrition/missingness, group count, and
model complexity. Simulation can be useful for hierarchy-aware designs. Power
0.80, alpha 0.05, 1,000 simulations, fixed MSRE, and cluster counts are not
defaults. A calculator is future work unless generic and entirely configured.

## 23. Missingness

Records retain explicit `not_evaluated`, `not_applicable`, `failed`,
`undefined`, `insufficient_data`, `unavailable`, and `uncalibrated` states.
Failures are not automatically MCAR/MAR/MNAR; that is an inferential
assessment. Future plans require missingness summaries and, where warranted,
sensitivity-analysis design. Zero filling is prohibited.

## 24. DQI validation requirements

DQI needs independently defined validation targets, dataset provenance,
human-reviewed semantic labels where relevant, held-out data, sensitivity to
normalization/embedding/threshold choices, ablation, uncertainty, and external
comparison. It must not validate the current composite with its own components.

## 25. Layer 2 validation requirements

Human/reference annotation must be independent. Reliability, judge-human
agreement, criterion validity, and calibration are distinct studies. Consensus
is a reference standard only when a protocol says so; agreement cutoffs are not
truth gates. Confidence calibration is meaningful only when confidence has a
defensible probabilistic interpretation.

## 26. BSDA validation requirements

Validation is component-specific: benign stability, matched perturbations,
construct-specific perturbations, repeated-generation stability, and convergent
or discriminant evidence are candidates. No composite, effect threshold, or
double-dissociation cutoff is authorized. Ablation evidence is conditional; a
single deletion result does not prove necessity.

## 27. RC validation requirements

RC needs meaningful prior degradation, an external compatible calibration
artifact for applicability, and retained context-window validity. Candidate
studies include synthetic trajectory sanity, controlled recovery, trajectory vs
terminal comparison, repeated-session stability, and truncation sensitivity.
No ROC-AUC is required without an independent binary criterion.

## 28. SAEA validation requirements

Candidate studies retain matched isolated/sequential contrasts, order
randomization where designed, homogeneous/heterogeneous attacks, stacked/spaced
conditions, sequence length, and repeated sessions. SI remains an empirical
candidate comparison: even an interval excluding one does not validate synergy.
Shapley attribution is not causal.

## 29. DRAA validation requirements

Only Mode A/B evidence fidelity, provenance, completeness, missingness, and
reproducibility are data-appropriate today. Risk prediction, ECE, BSS, and
other calibration thresholds are blocked pending future Mode C targets and
empirical calibration.

## 30. PRI validation requirements

Current studies may evaluate profile coverage, provenance, compatibility,
benchmark composition sensitivity, missingness, and future estimator
requirements. They must not estimate category robustness, weakest category,
scalar PRI, ranking, or rank-stability thresholds.

## 31. ML validation requirements

Future Phase 9E work needs independent labels, temporal admissibility, grouped
splits, attack/model/dataset holdouts, baselines, discrimination, calibration,
ablation, and distribution-shift evaluation. Phase 9B fixture results are not
data-ready validation and have no performance threshold.

## 32. Practical significance

Minimum relevant effects, equivalence/non-inferiority/superiority margins, and
utility functions are preregistration or calibration-dependent parameters.
Statistical significance below such a declared value is not automatically
“trivial,” nor can a generic cutoff make a result practically important.

## 33. Negative results

Non-significance is not equivalence, wide intervals indicate imprecision, and
conflicting results or failed replications must be reported. One failed ablation
does not automatically mark a component redundant; any status change requires
explicit scientific review/policy.

## 34. Statistical artifact schemas

Phase 10A may later define metadata-only `StatisticalAnalysisPlan`,
`StatisticalExperimentArtifact`, `HypothesisDefinition`, `EstimandDefinition`,
`AnalysisUnitDefinition`, `GroupingDefinition`, `ResamplingPlan`,
`MultiplicityPlan`, `EffectSizePlan`, `MissingnessPlan`, `AssumptionRecord`,
and `StatisticalResultRecord`. They must preserve experiment/hypothesis IDs,
component, readiness states, estimand, units, hierarchy, dataset/version/hash,
benchmark/model/taxonomy context, inclusion rules, method, assumptions, effect,
CI/resampling/multiplicity parameters, seed, software versions, missingness,
provenance, and result status. They contain no fabricated results or defaults.

## 35. Reproducibility

Plans record source versions/hashes, identities, declared configuration and
seeds, software versions, full grouping/pairing/split/resampling provenance,
and exclusions. Seeds support reproducibility but are not scientific constants;
perfect cross-platform determinism is not promised.

## 36. Staged Phase 10 implementation

Phase 10A plan/artifact infrastructure is **ENGINEERING_READY**: metadata and
validation only, no inference. Phase 10B descriptive/basic utilities are not
yet authorized as a blanket implementation; individual methods become
engineering-ready after method-specific contracts, numerical behavior, and
dependency decisions. Phase 10C hierarchy-aware inference, 10D component
validation runners, and 10E DRAA/PRI/ML scientific validation are future work
or blocked by data/labels/design.

## 37. Resolved decisions

Phase 10A is implementation-ready. Phase 10B is conditionally future work,
not a general authorization to add every candidate method. BCa, B >= 2,000,
and 95% intervals are not mandatory. LMM/GLMM does not replace ANOVA
universally; cluster-robust SE is not mandatory with mixed models. Alpha .05,
power .80, and VIF 5 are not project defaults. The rejected thresholds are
listed in Section 3.

No component-specific scientific validation is currently data-ready from the
repository alone: DQI lacks independent targets; Layer 2 lacks independent
reference protocol; BSDA/RC/SAEA lack approved empirical study data; DRAA/PRI
are uncalibrated; and ML has no real independent labels. Safe work is metadata,
descriptive engineering utilities under a later specification, and synthetic
protocol tests explicitly marked non-scientific.

## 38. Blockers

Blockers include missing claim-specific estimands, independent labelled data,
annotation/reference protocols, sampling design and hierarchy completeness,
preregistered inference/multiplicity/uncertainty choices, RC runtime data,
and dependency approval for advanced models. These are research decisions, not
implementation gaps to fill with examples.

## 39. Recommended immediate Codex scope

Implement Phase 10A only in a future task: immutable plan/provenance schemas,
explicit readiness/applicability states, deterministic serialization, and
schema validation. Do not compute tests, CIs, bootstrap results, mixed models,
or automatic scientific verdicts until a separately approved Phase 10B
specification supplies the method-specific design contracts.
