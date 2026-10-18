# Phase 9 ML prediction infrastructure

## Scientific role

Phase 9 adds provider-neutral ML schemas and a small CPU-only engineering
baseline. It distinguishes `engineering_ready`, label readiness, and validation
status. Executable training is not evidence that a real prediction target is
scientifically trainable or validated.

Phase 9A provides immutable contracts for `PredictionTask`, `TargetRecord`,
`FeatureRecord`, task-specific `FeatureSchema`, hierarchy identifiers,
`SplitPolicy`, `SplitManifest`, and experiment/model metadata. These records
preserve source-native semantics, provenance, timestamps, and explicit
non-value states. They do not manufacture hierarchy IDs or turn missing,
failed, unavailable, uncalibrated, or not-applicable values into zero.

Phase 9B trains only on explicitly synthetic fixtures or externally supplied
independently labelled data. Its implementation baseline is a training-label
only prevalence model and a deterministic L2 logistic regression. Both outputs
are marked `not_calibrated`; no calibration is performed.

## Timestamp, features, and admissibility

Every task declares a prediction stage: `pre_prompt_static`, `pre_generation`,
`post_response`, `historical_session`, `post_session`, or
`model_level_historical`. A feature schema applies to one task only. It defines
the ordered source-native feature set, type, allowed stage, missingness policy,
preprocessing, and admissibility decision.

Admissibility is a deterministic contract/provenance check, not statistical or
causal leakage discovery. It rejects features produced after the prediction
stage, schema-incompatible features, fields marked target/future dependent,
and prohibited fields. `DRAA.risk_score`, `PRI.scalar_pri`, and all PRI profile
features are excluded from Phase 9B case-level features. DRAA can only transport
evidence; duplicate direct and transported source provenance is warned about.

Layer 1 remains detector-native heuristic evidence, Layer 2 scores remain
dimension/rubric measurements rather than probabilities, BSDA retains four
separate components, and SAEA retains source-native cumulative vulnerability
rather than a hazard or composite. RC runtime features are not invented while
there is no typed RC runtime result.

## Grouped splitting and preprocessing

The default supported split is deterministic grouped holdout. The caller
chooses the grouping key, requested partitions, optional fractions, and seed;
there is no built-in 60/20/20 allocation or universal group key. A manifest
records both group and unit assignments and prevents a configured group from
crossing partitions.

Preprocessing is fitted from training records only. Numeric features use
training-only imputation and optional scaling plus an explicit missingness
indicator. Categorical features use training-only one-hot categories with an
unknown value. There is no target encoding, group-frequency encoding,
automatic transform selection, PCA, UMAP, or embeddings in Phase 9B.

## Metrics and artifacts

Binary-fixture metrics include prevalence, ROC-AUC, Average Precision, Brier,
log loss, precision, recall, F1, balanced accuracy, and MCC. Threshold metrics
are not computed without a caller-supplied threshold. One-class undefined
metrics remain explicitly undefined.

`MLExperimentArtifact` stores task/schema/split identities and hashes,
preprocessing and estimator configuration, seed, software versions, metrics,
label provenance, and scientific status. Synthetic labels require
`engineering_baseline_only`. `MLModelArtifact` is metadata for a possible
future persisted estimator and always records raw-output semantics and
calibration state.

Pickle/joblib-style model files can execute code during deserialization. Hashes
and manifests do not make an untrusted serialized model safe: such files must
only be loaded from trusted, verified provenance.

## Reproducibility

Use `python -m scripts.prediction_smoke` for a small deterministic synthetic
fixture. It creates a task/schema, generates a grouped manifest, trains only on
the train partition, and prints an engineering-baseline summary. Seeds,
schema hashes, split manifests, configurations, and Python version are retained
for audit, without promising cross-platform bit-for-bit determinism.

## What Phase 9 does not yet establish

- no validated real attack-success predictor;
- no hallucination predictor;
- no security-risk predictor;
- no validated recovery predictor;
- no calibration;
- no Random Forest, XGBoost, LightGBM, CatBoost, or MLP;
- no SHAP or feature-importance claim;
- no model ranking or predictive-usefulness claim; and
- no judge-as-ground-truth training.

Synthetic-data success validates engineering behavior only.
