# ML prediction implementation reconciliation

## 1. Authoritative ML role

This document is the Phase 9 implementation-safe contract. It reconciles the
ML prediction proposal with the current SecureLLMBench repository and the
approved upstream contracts. Where they differ, the current SecureLLMBench
contract wins.

The repository currently contains only `core.prediction.Predictor`, a minimal
future protocol. It has no target schema, feature schema, split machinery,
training pipeline, fitted estimator, or prediction experiment artifact. This
document therefore authorizes no application code by itself.

ML infrastructure being implementable is different from a scientifically
trainable or validated prediction task. A trained model is not evidence of
predictive usefulness without valid, independently defined outcome labels and
an appropriate held-out evaluation. Synthetic fixtures can validate engineering
behavior only.

Status words below have deliberately narrow meanings:

| Status | Meaning |
| --- | --- |
| **FORMALLY DEFINED** | Defined by an approved current contract. |
| **IMPLEMENTATION DEFAULT** | A reproducibility or engineering choice, explicitly configurable and not a scientific claim. |
| **CALIBRATION-DEPENDENT** | Requires a compatible, versioned external artifact or policy. |
| **EMPIRICAL HYPOTHESIS** | Requires a study; it is not an implementation assumption. |
| **DIAGNOSTIC** | Descriptive output, not a decision or target by itself. |
| **FUTURE WORK** | A plausible extension not in the current scope. |
| **BLOCKER** | Missing information prevents a scientifically meaningful implementation or use. |

## 2. Upstream contract corrections

### Layer 1

`DetectorResult` preserves detector name, unit score, optional confidence,
matched evidence, detector-native signal scores, and metadata. The aggregate
`LayerOneReport` preserves injection, leakage, jailbreak, aggregate, severity,
and a nullable `attack_success_signal`. It is `None` unless a caller supplies
an explicit project-specific rule. These are heuristic signals, not binary
truth labels or calibrated probabilities. Their thresholds, weights, and
severity mapping are configurable and unvalidated.

### Layer 2

`JudgeResult` is a dimension-specific measurement with a status, applicability
and reason, optional score/label/confidence, uncertainty reason, concise
rationale/evidence, provider/model/prompt/rubric/methodology versions,
generation metadata, run metadata, attempts, timestamp, and failure details.
The allowed dimensions are safety stance, correctness, consistency,
instruction following, hallucination, reasoning quality, and semantic drift.
Scores are not probabilities, are not ground truth, and a skipped, refused, or
failed dimension has no score. In particular, correctness cannot be evaluated
where required grounding is unavailable.

### BSDA

BSDA is an unvalidated component vector: **semantic**, **safety**,
**instruction**, and **structural**. Each component retains raw distance,
optional calibrated normalization, calibration status, optional confidence
interval, unmeasurability and its reason. `BSDAResult.composite` is always
`None`. The current contract contains no Jensen-Shannon divergence, ICC, or
BSDA composite, so none is a Phase 9 feature.

### RC

RC has an approved reconciliation specification but no current runtime package.
Its approved meaning is recovery after attack-induced degradation, not generic
next-step recovery probability and not attack success. Its primary output is
per-run `RC_AUC_raw` (with a bounded display value) and a secondary terminal
recovery result, along with the baseline, attack degradation, and recovery
trajectory. Scores require an external compatible calibration artifact; without
one, trajectories may be persisted but RC scores are null and uncalibrated.
Recovery latency and relapse are optional, calibration-controlled diagnostics.
No generic historical step-down rate or latency feature is approved.

### SAEA

SAEA is a provider-neutral sequential-evaluation contract, not a composite ML
score. Current outputs include a per-step deviation and context effect,
sequential trajectory, `cumulative_vulnerability`/`CV_obs`, candidate
Bliss-style synergy index, order effect, Shapley attribution, recovery trend,
isolated controls, context/spacing state, and explicit statuses. **CV_obs is
cumulative vulnerability, not cumulative hazard.** There is no approved
cumulative-hazard, step-out velocity, autocorrelation, or SAEA composite.
Future derived ML transformations would require their own versioned feature
contract and leakage review.

### DRAA and PRI

DRAA is Mode A/B lossless evidence transport and uncalibrated descriptive
diagnostics. `DRAAEvidenceRecord.risk_score` is always `None`. DRAA can carry
source-native evidence but is not a scalar ML feature or target.

PRI is Mode A/B profile infrastructure. `PRIProfileRecord.scalar_pri` is always
`None`. Its canonical profile axis is unresolved; the implementation is a
two-axis evidence/profile representation with an optional explicit construct
mapping, not an approved six-dimensional robustness vector.

## 3. Prediction units

**FORMALLY DEFINED:** an available benchmark unit is `EvaluationResult`, made
of an evaluation ID, case, terminal execution status, attempts, optional model
response, and optional error. The case carries dataset index, optional record
ID, prompt, and arbitrary metadata. The current dataset record has only
optional ID, prompt, category, attack type, source, language, difficulty, and
metadata.

The following hierarchy is a useful *optional* representation, not a required
existing key set: model configuration; benchmark/dataset; attack category;
attack family; base case; prompt variant; stochastic run; session/sequence; and
turn. `PRI.HierarchyIdentifiers` already permits several of these as nullable
values. A Phase 9 artifact must preserve missing identifiers explicitly rather
than fabricate them. Repeated generations do not become independent base cases
merely because they have distinct evaluation IDs.

## 4. Prediction timestamps

Every `PredictionTask` must explicitly declare a prediction timestamp/stage:
the moment at which features are available and the future observation to be
predicted. Suggested stage vocabulary is `pre_prompt_static`,
`pre_generation`, `post_response`, `historical_session`, `post_session`, and
`model_level_historical`; it is a controlled implementation vocabulary, not a
claim that all stages are available for every task.

No universal feature matrix is admissible. A feature is admissible only when it
was available no later than that task's declared timestamp, has no direct or
proxy access to the target outcome, and its provenance establishes this.

## 5. Target readiness

| Candidate target | Task schema | Valid labels | Empirically trainable now | Validated | Status / blocker |
| --- | --- | --- | --- | --- | --- |
| Category-specific attack outcome | IMPLEMENTATION-ready | LABEL-DEPENDENT | No repository labels | No | **BLOCKER**: outcome definition and independently labelled cases. |
| Prompt-injection success | IMPLEMENTATION-ready | LABEL-DEPENDENT | No | No | Requires attack-family success criteria and labels. |
| Verified canary leakage | IMPLEMENTATION-ready | Potentially deterministic when a known expected canary is declared before evaluation | Not currently represented as a target dataset | No | A fixture/protocol may supply label evidence; generic leakage signals do not. |
| Jailbreak/policy violation | IMPLEMENTATION-ready | LABEL-DEPENDENT | No | No | Requires scoped policy and independently verified labels. |
| Hallucination | Schema conditional | BLOCKED without grounding/reference labels | No | No | Layer 2 hallucination measurement is not a truth label. |
| Security risk | No approved scalar target | BLOCKED | No | No | DRAA risk score is null; no risk-label definition/calibration exists. |
| Recovery | Schema conditional | LABEL-DEPENDENT and protocol-dependent | No | No | Needs approved RC runtime protocol and labels/calibration; RC is not generic recovery probability. |

There is no global `attack_success` label. Category-specific labels must state
the attack family, success criterion, evidence/adjudication procedure, label
version, and applicability. Human annotation is not automatically approved by
the current contracts. If introduced, adjudication must be explicit and
agreement measured and reported. Proposed Cohen/Fleiss kappa cutoffs (including
0.80 and 0.75) are **EMPIRICAL HYPOTHESES**, not hard-coded truth criteria;
study-specific preregistration or calibration would be required.

## 6. Ground-truth requirements

Every `TargetRecord` must contain target name and schema/version, unit ID,
value or explicit non-value status, label source, applicability, evidence or
adjudication provenance, timestamp, and hierarchy/group identifiers available
for splitting. Labels must distinguish missing/not evaluated, not applicable,
failed, undefined, insufficient data, unavailable, and uncalibrated; no status
may be silently mapped to class zero.

Direct deterministic verification is preferred where the task protocol permits
it, such as expected-canary matching known before execution. It is still
task-specific evidence, not a licence to turn every detector score into truth.
All other real targets need a documented reference or human/independent
adjudication protocol and held-out evaluation plan before scientific use.

## 7. Feature taxonomy and definitions

`FeatureRecord` must identify the feature schema/version, name, source
namespace and artifact ID, raw value, value type/units/orientation, semantic
status and reason, availability stage, extraction timestamp, and provenance.
It should classify each feature as one of: pre-prompt/static, pre-generation,
post-response, historical-session, post-session, model-level historical,
unavailable, or target-leaking.

Allowed Phase 9 feature sources are only source-native upstream values with
their current meanings:

- dataset fields and processing statistics available at the selected stage;
- benchmark case and response execution metadata, including latency and token
  usage when provided by a provider;
- Layer 1 detector-native scores/signals/evidence/statuses;
- Layer 2 dimension-specific result fields, retaining status, applicability,
  confidence, uncertainty, and provenance;
- distinct BSDA components and their raw/normalized/calibration states;
- approved RC trajectory fields only once an RC artifact exists; and
- distinct SAEA outputs, including status and the non-hazard meaning of CV_obs.

JSD-style BSDA features, SAEA cumulative hazard, step-out velocity,
autocorrelation, generic RC rate/latency, Layer 2 probabilities, and a PRI 6D
vector are **FUTURE WORK**, not Phase 9 definitions. PCA, if later selected, is
unsupervised dimensionality reduction; it is not supervised.

## 8. Feature admissibility and leakage controls

Admissibility is target- and timestamp-specific. A Phase 9 feature schema must
record an explicit decision for every feature: admitted, unavailable, or
excluded as target-leaking, plus the reason. Preprocessing, embedding, and
feature selection must be fitted only on the training partition. Validation and
test labels must never influence feature fitting, transformation selection,
threshold selection, or calibration.

DRAA evidence must not duplicate direct evidence: a direct Layer 1 feature and
the same Layer 1 feature carried by DRAA are one measurement, not two columns.
DRAA's role is evidence transport/provenance. PRI is excluded from ordinary
case-level baseline ML by default. Any future historical PRI-derived feature
requires disjoint source cases, explicit temporal ordering, out-of-fold or
nested construction, and provenance proving no test contamination.

## 9. Hierarchical grouping, split policies, and cross-validation

`SplitPolicy` must state its unit, selected group key(s), partition intent,
random seed if used, and rationale. `SplitManifest` must persist the resolved
unit-to-partition assignment, group values, dataset/benchmark hashes, feature
and target schema versions, policy version, and generation provenance.

Grouped splitting is the appropriate default scientific posture, but no single
group field or 60/20/20 allocation is formally correct. Task-specific candidates
include grouped base-case, attack-family, dataset, model-family, and
temporal/version holdout. Random row splitting may exist only as a clearly
labelled diagnostic leakage baseline, never as the default scientific split.

A configuration-driven grouped-CV interface may support `GroupKFold` and
`StratifiedGroupKFold` where their prerequisites hold. The number of folds must
be selected from group count, class support, sample size, and computation, then
recorded. Nested CV is optional future work; fixed 5x5 nested CV is rejected.

## 10. Preprocessing, missingness, and embeddings

The minimal leakage-safe baseline is:

- Numeric: preserve semantic status; represent missingness explicitly; perform
  training-fold-only imputation only when an estimator requires finite values;
  use scaling for logistic regression.
- Categorical: safe one-hot encoding with unknown-category handling.

No skewness cutoff, universal RobustScaler rule, variance cutoff, target
encoding, group-frequency encoding, or transform is approved as a scientific
default. Any enabled transformation must be configuration- and
provenance-tracked. Target encoding is outside the baseline scope because of
its additional leakage risk.

Dense embeddings are **FUTURE WORK** for Phase 9A/B unless a task requires
them. Any later embedding feature needs source text, embedding model/version,
timestamp, dimensionality, training-only fitted transformation, and provenance.
There is no approved 16-dimensional cap, variance-retention target,
768-dimension trigger, or UMAP requirement.

## 11. Algorithms, metrics, thresholds, and calibration

For a Phase 9B engineering experiment with synthetic or independently labelled
fixtures, the exact initial algorithm set is:

1. constant/prevalence baseline; and
2. L2-regularized logistic regression with configuration-recorded
   preprocessing.

This is an **IMPLEMENTATION DEFAULT**, not a claim of estimator superiority.
Random Forest is Phase 9C optional secondary work after the baseline experiment
contract is proven. XGBoost, LightGBM, CatBoost, and MLP are future/optional;
they are not production defaults and should not be installed now.

Potential evaluation metrics are ROC-AUC, PR-AUC/Average Precision, Brier score,
log loss, precision, recall, F1, balanced accuracy, and MCC. A task must choose
metrics based on target semantics, prevalence, and decision use and record that
choice. One-class partitions make several metrics undefined; undefined remains
undefined, not zero. Class prevalence and majority-class predictions are valid
classification baselines. A Layer 1-only baseline must be explicitly specified
as detector-rule or learned and retains its non-ground-truth nature. A raw
Layer-2 threshold of 0.5 is rejected because judge scores are neither calibrated
probabilities nor necessarily similarly oriented.

Operational decision thresholds are absent unless externally supplied,
preregistered, or validation-selected under an explicit utility/cost definition.
No `C_FN = 10 * C_FP` rule is approved. Threshold-independent metrics are
sufficient for Phase 9B.

Calibration capability is deferred to Phase 9D. It must distinguish raw score
from calibrated probability, train without test labels, record calibration
status and method, and select sigmoid/Platt versus isotonic empirically or by
configuration rather than a fixed sample cutoff. ECE is optional and
bin-sensitive; its binning/reliability-curve configuration must be recorded.
Brier and log loss can be used without binning.

## 12. Uncertainty, interpretability, imbalance, and tuning

Confidence intervals, bootstrap resample counts, confidence levels, and seeds
are not prescribed as scientific defaults. Phase 9A/B must preserve group IDs
needed for later uncertainty, but need not produce intervals for synthetic
baseline tests. Repeated generations may be reported as descriptive variability;
they must not be labelled aleatoric uncertainty without an explicit model.

Permutation importance is optional future diagnostic and requires warnings for
correlated features; it is not causal. SHAP is optional, not a core dependency,
and has no fixed background size. Linear coefficients can be the simpler
diagnostic for a logistic baseline.

Class weighting is configuration-dependent. Report original target prevalence.
Resampling such as SMOTE is excluded from baseline scope because naive grouped
text resampling is risky; if later used, it must occur training-only. Tuning is
future work: no Optuna mandate, 50-trial count, fixed PR-AUC optimization, or
nested-CV requirement is approved. No test-set reuse is permitted.

## 13. Experiment and model artifacts

Phase 9A schemas should be implementation-ready but need not store fitted
models:

- `PredictionTask`: target schema/version, prediction timestamp/stage, unit,
  declared task type, admissibility policy, group requirements, and provenance.
- `FeatureRecord` and `FeatureSchema`: as defined above, including source
  contracts, semantic status, transformation provenance, and schema/hash.
- `TargetRecord`: label value/status, label/evidence schema, applicability,
  timestamp, and provenance.
- `SplitPolicy` and `SplitManifest`: declared grouping and resolved, auditable
  assignment without fabricated IDs.
- `MLExperimentArtifact`: dataset/benchmark hashes, model/configuration
  population, target and feature schemas/hashes, split provenance, seed,
  software versions, estimator/preprocessing configuration, results, and
  scientific-status disclaimer.
- `MLModelArtifact` metadata: the same identities plus raw-versus-calibrated
  output semantics, calibration status, serialization format/hash, dependency
  versions, and trusted-provenance requirement.

Python estimator objects serialized with pickle/joblib can execute code on
load. They must only be loaded from trusted, verified provenance. A manifest,
hashes, dependency versions, schema versions, and split provenance are required
alongside any future persisted estimator; these controls do not make arbitrary
untrusted deserialization safe.

## 14. Reproducibility and safe phases

Seeds are configurable reproducibility inputs, not scientific constants. Record
the effective seed, Python/library versions, feature-schema/version/hash,
dataset/benchmark hashes, split manifest, estimator configuration, and
preprocessing configuration. Do not promise bit-identical output across every
library or hardware configuration.

| Phase | Scope | Status |
| --- | --- | --- |
| 9A | Schemas, timestamp/admissibility, hierarchy IDs, split-policy/manifest, and experiment/model metadata; no training. | **IMPLEMENTATION-ready**. |
| 9B | Synthetic or independently labelled fixture baseline with prevalence and L2 logistic regression, leakage-safe preprocessing, grouped split, basic metrics, and provenance. | **IMPLEMENTATION-ready only as engineering infrastructure**; no real predictive-usefulness claim. |
| 9C | Random Forest and optional external advanced estimators after dependency and experiment review. | **FUTURE WORK**. |
| 9D | Calibration capability and diagnostics, optional permutation importance/SHAP. | **FUTURE WORK**. |
| 9E | Independently labelled outcomes, grouped generalization, model/attack/dataset holdouts, ablations, uncertainty, and distribution shift. | **BLOCKER** for scientific validation. |

## 15. Resolved decisions

1. Phase 9A is implementation-ready: it is schema/provenance infrastructure
   only, not a training claim.
2. Phase 9B is implementation-ready solely for synthetic or independently
   labelled fixtures. It is not ready to establish predictive usefulness on
   current repository data.
3. No general real supervised target is currently trainable from repository
   artifacts. A known-a-priori canary protocol could supply a future
   category-specific label dataset, but none currently exists.
4. Attack-family outcomes remain label-dependent; hallucination is blocked
   without grounding/reference labels; security risk is blocked; recovery is
   target- and RC-protocol-dependent.
5. Phase 9B contains only the constant/prevalence baseline and L2 logistic
   regression.
6. Calibration is deferred to Phase 9D.
7. Random Forest is Phase 9C optional secondary work.
8. XGBoost, LightGBM, and CatBoost must not be implemented now.
9. DRAA contributes evidence transport/provenance only; it supplies no scalar
   risk feature and must not duplicate direct upstream measurements.
10. PRI is excluded from baseline case-level ML by default.
11. Rejected Gemini numeric/statistical defaults: 60/20/20 splitting; 5x5
   nested CV; kappa 0.80/0.75 truth cutoffs; Layer-2 threshold 0.5;
   `C_FN = 10 * C_FP`; skewness >2, RobustScaler, and variance <1e-5 rules;
   PCA/embedding dimension and variance cutoffs; ECE 10 bins; repeated-run,
   bootstrap, and CI defaults as scientific truths; fixed SHAP background;
   fixed imbalance/prevalence rules; Optuna/50 trials; and fixed calibration
   sample cutoffs.
12. The immediately safe engineering scope is exactly Phase 9A and, after it,
   a Phase 9B fixture-only baseline with explicit target, feature,
   timestamp/admissibility, group split, preprocessing, metric, provenance, and
   non-validation contracts. It must make no scientific predictive claim.

## 16. Blockers and open questions

The blockers for real ML research are: approved outcome definitions by attack
family; independently labelled and adjudicated data; a hierarchy complete enough
for the selected generalization question; a prespecified split and metric plan;
task-specific feature availability; treatment of repeated generations;
calibration/threshold/utility policies where decisions are needed; and
independent validation under attack, model, dataset, and distribution shift.

Open questions are research questions, not omissions that an engineer may fill
with numeric defaults. They include the exact target populations, ground-truth
protocols, calibration populations, selected group key for each task, whether
embeddings add reproducible value without leakage, and which decision use (if
any) warrants an operational threshold.
