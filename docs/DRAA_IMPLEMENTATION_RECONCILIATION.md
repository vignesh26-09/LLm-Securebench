# DRAA Implementation Reconciliation

**Status:** Specification review only. No DRAA application code is authorized by this document.

This document reviews `DRAA_RECONCILED_FORMAL_SPEC.md` against the actual Layer 1, Layer 2, BSDA, RC, and SAEA contracts. DRAA must preserve upstream meanings, applicability, uncertainty, and provenance. It must not redefine any metric, zero-fill unavailable evidence, treat a judge as ground truth, or claim scientific validation.

## 1. Authoritative DRAA definition

The source proposes `V = P(safety failure | available evidence)`. DRAA is intended as heterogeneous evidence aggregation and calibration, not token-level trajectory analysis and not a replacement for BSDA, RC, or SAEA.

**Classification: BLOCKER.** “Safety failure” currently combines attack success, safety-boundary failure, recovery failure, and systematic behavioral deviation. These are distinct constructs: attack success needs a threat-model-specific outcome; deviation is not inherently safety failure; RC can be unavailable when no initial degradation was measurable. No label policy, annotation protocol, or adjudication rule defines positives. Thus it is not currently a supervised/calibrated probability target.

`P(safety failure | X)` may only be a future target after a versioned label definition and labelled data exist. It is not an output Phase 0 evidence can justify.

## 2. Upstream metric contracts

| Source | Contract DRAA must preserve | DRAA feature status |
| --- | --- | --- |
| Layer 1 | Detector signals with score/confidence/evidence/metadata; signals are not ground truth and are uncalibrated. | Candidate evidence only; no universal normalization. |
| Layer 2 | Dimension-specific `[0,1]` judge measurements with applicability, confidence, uncertainty, model/prompt/rubric version, and failures. | Candidate dimension features; never truth labels. |
| BSDA | Four separate components with raw distance, optional calibration/normalization, CI, and applicability. No composite is approved. | Preserve each applicable component separately. |
| RC | Raw/bounded recovery and terminal values conditional on calibration and measurable degradation; can be not-applicable, uncalibrated, incompatible, or undefined. | Preserve values/status; no inferred risk direction. |
| SAEA | Vector of context effects, `CV_obs`, candidate SI, order effects, RC trend, length analysis, and Shapley attribution. | Select preregistered compatible candidates; never flatten wholesale. |
| Severity | External harm/impact assessment, distinct from failure probability. | Separate reporting now; possible later expected-risk input. |

**Classification: FORMALLY DEFINED** for identity/provenance; **BLOCKER** for a shared scalar scale.

## 3. Risk target

An engineer can represent a proposed target as an immutable `SafetyFailureLabelArtifact` containing case/attack IDs, threat model, definition version, annotator/adjudication provenance, status, dataset version, and disagreement/uncertainty. This is a schema recommendation only; it does not define labels.

Before scalar prediction, the project must resolve: the observable positive outcome; which inputs may define labels without leaking into predictors; how ambiguity/refusal/not-applicability are labelled; and how ground truth/disagreement are collected.

**Classification: BLOCKER.**

## 4. Feature schema

The implementation-ready result is `DRAAEvidenceRecord`, not a risk score. It contains typed `EvidenceFeature` records with feature namespace/name, scalar/vector value without forced conversion, source scale/orientation, status/reason, supplied CI/SE/confidence, failure data, case/run/sequence/model/dataset/threat IDs, source artifact IDs, provider/prompt/rubric/calibration provenance, and a missingness indicator that distinguishes not-applicable, uncalibrated, failed, undefined, insufficient-data, and absent.

Candidate fields are Layer 1 detector results; completed Layer 2 dimensions/confidence; individual BSDA components; RC values/status; selected SAEA results; and a separate severity field. No scalar may be manufactured when upstream evidence is unavailable.

**Classification: IMPLEMENTATION DEFAULT.** It is lossless and makes no aggregation claim.

## 5. Scale and orientation rules

No approved cross-metric normalization contract exists.

- **Layer 1:** score scales vary by detector. Percentile transforms need a versioned reference distribution and population.
- **Layer 2:** scores are `[0,1]`, but orientation is dimension/rubric-dependent; confidence is not probability calibration.
- **BSDA:** retain raw and optional artifact-normalized component values. No DRAA-created composite.
- **RC:** higher raw recovery means greater recovery, not automatically greater risk. Do not use `1 - RC`: RC can be negative/undefined and no recovery-to-failure mapping is approved.
- **SAEA:** `CV_obs`, SI, context effects, order results, recovery trends, length fits, and Shapley values have different units/conditions and are not mutually exchangeable.
- **Severity:** impact is not failure probability.

Empirical scaling, orientation transforms, percentile parameters, and reference populations require a compatible calibration artifact; none may be hard-coded.

**Classification: BLOCKER** for scalar aggregation; **CALIBRATION-DEPENDENT** for later normalization.

## 6. Applicability and missingness

RC not-applicable/uncalibrated/incompatible/undefined states remain distinct. SAEA is structurally unavailable for single attacks and undefined SI is not zero. Failed/skipped/refused Layer 2 judgments are not numeric scores. BSDA failures are per-component unmeasurable. Missing uncertainty is unknown, not a zero-width interval.

Separate models by evidence pattern, explicit missingness indicators, and marginal models are possible future strategies, but none is approved. Imputation is prohibited.

**Classification: FORMALLY DEFINED** for preservation; **BLOCKER** for scalar-model missingness treatment.

## 7. Dependence handling

Known dependence includes Layer 1/2, BSDA/Layer 2, BSDA/RC, and BSDA/SAEA. The source proposes correlation screening, regularization, hierarchical grouping, and Bayesian priors as candidates but selects no primary model. `R_fast = combine(Layer1, Layer2)` and `R_beh = consensus(BSDA, RC, SAEA)` are undefined operators.

The `0.5 * R_fast + 0.5 * R_beh` example is **rejected as an implementation default**. It is illustrative only and arbitrary absent learned/calibrated justification. Rules like dropping a feature at `rho > 0.70` are provisional experimental heuristics at most, not DRAA rules.

**Classification: BLOCKER** for scalar aggregation. Feature-correlation matrices and missingness summaries are **DIAGNOSTICS** once data exists, without feature removal implied.

## 8. Severity handling

Severity remains separate from evidence of safety failure. It must not be mixed into a probability target without a defined causal/predictive role.

Future expected risk could be `calibrated failure probability * calibrated impact`, but needs an impact scale, severity mapping, outcome taxonomy, and utility rule. None is approved.

**Classification: FORMALLY DEFINED** for separation; **FUTURE WORK** for expected risk; **BLOCKER** for severity inside the current scalar.

## 9. Dynamic interpretation

Bayesian posterior updating is conceptual, not a formal DRAA model. It needs a prior, calibrated likelihood/observation model per feature, arrival order, dependence treatment, posterior algorithm, and credible-interval semantics. Scores in `[0,1]` are not likelihoods merely by being bounded.

Token-level trajectories are a separate optional diagnostic, not primary DRAA input/output.

**Classification: FUTURE WORK.**

## 10. Uncertainty

Upstream uncertainty is preserved losslessly in an evidence record. Existing specifications supply no common joint distribution, covariance model, label model, estimator, or transform enabling bootstrap propagation, delta-method intervals, posterior intervals, or prediction intervals for DRAA.

`estimate ± 1.96 * SE` is not approved: normality, independence, and a scalar estimator are not established. RC/SAEA bootstrap defaults apply only to their own defined statistics.

**Classification: FORMALLY DEFINED** for retaining upstream uncertainty; **BLOCKER** for scalar uncertainty.

## 11. Calibration artifact

A future immutable/versioned `DRAACalibrationArtifact` needs DRAA methodology/model and label-definition versions; upstream schemas/providers/prompts/rubrics/calibrations; feature selection/scales/orientations/reference population; dataset/model/threat coverage and splits; learned model/coefficient/hyperparameter provenance; calibration method/results; uncertainty, dependence, and missingness policies; training/evaluation provenance, seeds, timestamps, and validation status.

Without a compatible artifact, output must be `UNCALIBRATED` evidence/provenance—not a probability-like scalar.

**Classification: CALIBRATION-DEPENDENT.**

## 12. Implementation modes

| Mode | Permitted output | Status |
| --- | --- | --- |
| A — feature extraction | Typed evidence vector plus applicability, uncertainty, and provenance. | IMPLEMENTATION-READY |
| B — uncalibrated research representation | Evidence summaries/dependence/missingness diagnostics; no scalar risk. | IMPLEMENTATION-READY |
| C — calibrated learned prediction | Target-specific probability plus uncertainty from a compatible artifact. | BLOCKED pending target, labels, fitted model, and validation. |

Modes A/B must label results `UNCALIBRATED`; neither may call a summary a safety-failure probability.

## 13. Validation requirements

After target/calibration exist, compare severity only, each individual source, a transparent simple baseline, learned logistic regression, and final DRAA. Require grouped cross-validation; model-family, attack-family, and dataset holdouts; calibration curves; Brier/log loss; ROC-AUC/PR-AUC when suitable; CIs; ablations; dependence analysis; and leakage prevention.

Preprocessing, feature selection, calibration, and normalization must fit inside training folds. Grouping must prevent attack-family, sequence/session, model-run, or near-duplicate leakage. Sample sizes and performance thresholds are empirical study decisions, not universal requirements.

**Classification: EMPIRICAL HYPOTHESIS / FUTURE WORK.**

## 14. Resolved decisions

| Question | Reconciliation | Classification |
| --- | --- | --- |
| Primary role | Evidence representation/calibration framework, not token trajectory or metric replacement. | FORMALLY DEFINED |
| 0.5/0.5 | Illustrative only; rejected as default. | FORMALLY DEFINED |
| BSDA input | Preserve four components; no new composite. | FORMALLY DEFINED |
| RC orientation | Preserve raw/bounded/status; do not invert into risk. | FORMALLY DEFINED |
| SAEA input | `CV_obs`/SI are candidate sequence evidence; per-step/order/Shapley/length/recovery fields are diagnostic/statistically conditional; no wholesale flattening. | FORMALLY DEFINED |
| Severity | Separate impact field, not probability evidence by default. | FORMALLY DEFINED |
| Uncalibrated mode | Evidence record and `UNCALIBRATED`; no scalar risk. | IMPLEMENTATION DEFAULT |

## 15. Implementation-blocking ambiguities

1. Threat-model-scoped ground-truth definition and annotation/adjudication protocol for safety failure.
2. Non-arbitrary calibrated formula/model for `R_fast`.
3. Non-arbitrary calibrated formula/model for `R_beh`.
4. Compatible normalization/direction contract, including RC orientation and selected SAEA features.
5. Approved missingness/dependence treatment for prediction.
6. Scalar uncertainty estimator with justified assumptions.
7. Severity role and, for expected risk, an impact mapping/utility rule.
8. For Bayesian dynamics: priors, likelihoods, order, dependence model, algorithm, and calibration validation.

## 16. Recommended next step

**DRAA scalar aggregation is not implementation-ready.**

The next safe scope is provider-neutral Mode A/B evidence schemas and serialization that preserve upstream values/statuses/uncertainty/provenance without calculating risk. In parallel, define and preregister ground truth, label collection, splits, feature availability, and calibration-artifact contracts. Only then design and validate a Mode C scalar predictor.
