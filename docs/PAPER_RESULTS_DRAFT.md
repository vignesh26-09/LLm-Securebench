# Results Draft (Evidence-Constrained)

## System and traceability results

SecureLLMBench implements an evaluation record pipeline that preserves model
configuration, benchmark execution artifacts, Layer 1 detector outputs,
structured scientific-record families, and readiness metadata. The resulting
artifact chain permits a reader to distinguish an observed local execution
from a calibrated empirical conclusion. Table 1 summarizes the component
families, their unit of analysis, and their validation status. Figure 1 shows
the corresponding pipeline, while Figure 3 identifies the gates that prevent
unsupported conclusions from being represented as validated outcomes.

## JailbreakBench judge-comparison calibration

We verified a persisted judge-comparison analysis against the recorded
JailbreakBench source revision and checksum. Of 300 source records, 295 were
usable paired records, giving 98.333% coverage. Under the fixed predeclared
mapping, raw agreement between the current Gemma-based judge and the recorded
human outcome was 53.898%, with Cohen's kappa of 0.211261. The confusion matrix
contained 51 predicted-0/human-0 records, one predicted-0/human-1 record, 135
predicted-1/human-0 records, and 108 predicted-1/human-1 records (Table 2 and
Figure 2).

These values do not validate the judge as a replacement for independent human
outcome labels. The observed disagreement is strongly asymmetric, but this
analysis does not establish its cause. We therefore retain the human outcome
as the independent reference and treat the judge output as uncalibrated for
replacement use.

## Local engineering demonstration

The local execution record contains one dataset/version, two model
configurations (`qwen3.5:2b` and `gemma3:4b`), four runs, 12 evaluations, and
36 Layer 1 records. It also contains 25 scientific records, zero dashboard
Layer 2 records, and two engineering detector-summary model scores (Table 3).
This result demonstrates local software execution and artifact capture. The
small trace does not support a scientific comparison, ranking, percentage
estimate, or safety conclusion for either model.

## Measurement readiness

The evidence bundle reports implemented measurement families without turning
their current outputs into unsupported results. BSDA retains four components
without a composite score. RC remains a raw, calibration-dependent trajectory.
SAEA's observed cumulative-vulnerability output is not an attack-success rate,
and its candidate Bliss analysis remains experimental. DRAA Modes A and B are
diagnostic and uncalibrated, while Mode C is unavailable. PRI is a profile
without a scalar grade or ranking. DQI is exploratory. ML has implementation
infrastructure but lacks production labels and validated predictive evidence;
the statistics infrastructure likewise supports no inferential claim.
