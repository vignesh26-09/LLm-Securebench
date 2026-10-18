# Abstract Facts and Constraints

## Facts available for an abstract

- SecureLLMBench implements a traceable and evidence-status-aware LLM security
  evaluation workflow.
- The system records benchmark configurations, execution traces, evaluations,
  Layer 1 observations, structured measurement records, and validation status.
- A persisted JailbreakBench judge-comparison calibration contains 300 source
  records and 295 usable records (98.333% coverage).
- Under its fixed predeclared mapping, the analysis reports 53.898% raw
  agreement and Cohen's kappa of 0.211261 for the current Gemma-based judge.
- The current judge is not sufficiently validated to replace independent human
  outcome labels.
- A local engineering demonstration records two configurations, four runs, 12
  evaluations, and 36 Layer 1 records.

## Abstract claims prohibited by the evidence

- “Validated judge,” “human-equivalent judge,” or “automated replacement for
  human labels.”
- Any model ranking, relative-safety result, ASR, calibrated risk, or security
  percentage based on the local demonstration.
- Any predictive-ML, inferential-statistics, novelty, significance, or
  generalization conclusion.

## Safe abstract structure

State the framework objective, traceability implementation, calibration
setting and exact measured values, conservative interpretation, and the
conclusion that evidence-status gates preserve the boundary between observed
engineering output and validated scientific claims.
