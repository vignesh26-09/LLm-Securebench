# SecureLLMBench Final Paper Handoff

## Purpose and permitted framing

SecureLLMBench is a validation-aware, traceable framework for recording LLM
security-evaluation inputs, execution traces, structured measurements, and
evidence status. The paper can describe an implemented system and a measured
judge-comparison calibration study. It must distinguish engineering evidence
from validated security conclusions.

Suggested working title: *SecureLLMBench: A Validation-Aware Framework for
Traceable LLM Security Evaluation*. This is a framing suggestion, not an
empirical claim.

## Contributions that the evidence supports

1. **Traceable evaluation framework (engineering contribution).** The system
   records benchmark configuration, model runs, evaluations, Layer 1 detector
   outputs, and scientific-record status so that result provenance can be
   inspected.
2. **Validation-aware safeguards (engineering contribution).** The system
   retains evidence-status fields and blocks unsupported presentation of
   uncalibrated measurements as validated risk, safety, or attack-success
   outcomes.
3. **Judge-calibration evidence (empirical contribution).** A persisted
   JailbreakBench judge-comparison analysis contains 300 source records and
   295 usable paired records under a fixed predeclared mapping.
4. **Local pipeline demonstration (engineering contribution).** Two local
   models, two configurations, four runs, 12 evaluations, and 36 Layer 1
   records demonstrate that the trace and measurement pipeline executes
   locally.
5. **Metric-readiness accounting (methodological/engineering contribution).**
   The paper can report which implemented metric families are exploratory,
   uncalibrated, blocked, or unavailable for scientific interpretation.

## Verified judge-comparison result

| Quantity | Verified value |
|---|---:|
| Source records | 300 |
| Usable paired records | 295 |
| Coverage | 98.333% |
| Raw agreement | 53.898% |
| Cohen's kappa | 0.211261 |
| Predicted 0 / human 0 | 51 |
| Predicted 0 / human 1 | 1 |
| Predicted 1 / human 0 | 135 |
| Predicted 1 / human 1 | 108 |

The supported interpretation is narrow: under the fixed predeclared mapping,
the current Gemma-based judge is **not sufficiently validated to replace
independent human outcome labels**. The disagreement is strongly asymmetric;
this descriptive observation must not be promoted to a causal claim about
bias. Raw agreement must not be described as better than random.

## Local engineering demonstration

The persisted local demonstration contains one dataset/version, two model
configurations (`qwen3.5:2b` and `gemma3:4b`), four runs, 12 evaluations, 36
Layer 1 records, zero dashboard Layer 2 records, 25 scientific records, and
two engineering detector-summary model scores. It is evidence that the local
software path executed. It is not a model comparison, ranking, percentage
claim, attack-success-rate study, or human-labelled safety study.

## Claims that must not appear as results

- No claim that any judge replaces, matches, or is validated against human
  labels beyond the measured calibration values above.
- No model ranking, winner, safer-model claim, or percentage comparison from
  the three-case local pilot.
- No attack success rate, risk probability, calibrated risk score, security
  grade, or composite score.
- No claim that Layer 1 detector outputs are ground truth.
- No inferential-statistics, predictive-ML, novelty, significance, or
  generalization claim.

## Evidence entry points

Use [PAPER_EVIDENCE_MANIFEST.md](/F:/SecureLLM/docs/PAPER_EVIDENCE_MANIFEST.md),
[PAPER_FREEZE_REPORT.md](/F:/SecureLLM/docs/PAPER_FREEZE_REPORT.md), and the
machine-readable files in [artifacts/paper_evidence](/F:/SecureLLM/artifacts/paper_evidence)
as the authoritative evidence bundle. The claim-by-claim writer guidance is
in [PAPER_CLAIM_EVIDENCE_MATRIX.md](/F:/SecureLLM/docs/PAPER_CLAIM_EVIDENCE_MATRIX.md).
