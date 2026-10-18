# Table and Figure Captions

## Table 1

**SecureLLMBench components, units of analysis, outputs, and validation
status.** The table distinguishes implemented engineering components from
calibrated scientific evidence. A component's presence does not imply that its
output is validated as ground truth, risk, attack success, or a model score.

## Table 2

**JailbreakBench judge-comparison calibration under a fixed predeclared
mapping.** The persisted analysis contains 300 source records and 295 usable
paired records (98.333% coverage). Raw agreement is 53.898% and Cohen's kappa
is 0.211261. The result indicates that the current Gemma-based judge is not
sufficiently validated to replace independent human outcome labels.

## Table 3

**Local engineering demonstration inventory.** The record contains two local
model configurations, four runs, 12 evaluations, 36 Layer 1 records, zero
dashboard Layer 2 records, 25 scientific records, and two engineering
detector-summary model scores. It demonstrates pipeline execution only and is
not a scientific model comparison.

## Figure 1

**SecureLLMBench traceability architecture.** Configuration and dataset inputs
flow through benchmark execution, evaluation records, Layer 1 observations,
structured measurements, and evidence-status gates. The architecture retains
provenance and prevents unsupported interpretation at reporting time.

## Figure 2

**Judge-versus-human confusion matrix for the persisted JailbreakBench
calibration.** Counts are 51 predicted-0/human-0, one predicted-0/human-1,
135 predicted-1/human-0, and 108 predicted-1/human-1 among 295 usable records.
The plot documents agreement structure; it does not demonstrate human-equivalent
judge performance.

## Figure 3

**Validation and readiness gates for scientific reporting.** The diagram marks
where uncalibrated detector outputs, exploratory metrics, unavailable modes,
and absent production labels block claims about ground truth, risk, attack
success, ranking, prediction, or inference.
