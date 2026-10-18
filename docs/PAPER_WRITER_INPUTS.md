# Paper Writer Inputs

## Authoritative evidence package

Use these files as the source of record for numerical statements and evidence
status:

1. [PAPER_EVIDENCE_MANIFEST.md](/F:/SecureLLM/docs/PAPER_EVIDENCE_MANIFEST.md)
2. [PAPER_FREEZE_REPORT.md](/F:/SecureLLM/docs/PAPER_FREEZE_REPORT.md)
3. [table1_components.csv](/F:/SecureLLM/artifacts/paper_evidence/table1_components.csv)
4. [table2_jbb_calibration.csv](/F:/SecureLLM/artifacts/paper_evidence/table2_jbb_calibration.csv)
5. [table3_local_engineering.csv](/F:/SecureLLM/artifacts/paper_evidence/table3_local_engineering.csv)
6. [table_data.json](/F:/SecureLLM/artifacts/paper_evidence/table_data.json)
7. [calibration_verification.json](/F:/SecureLLM/artifacts/paper_evidence/calibration_verification.json)
8. [figure1_architecture.svg](/F:/SecureLLM/artifacts/paper_evidence/figure1_architecture.svg)
9. [figure2_judge_human_confusion.svg](/F:/SecureLLM/artifacts/paper_evidence/figure2_judge_human_confusion.svg)
10. [figure3_readiness_gates.svg](/F:/SecureLLM/artifacts/paper_evidence/figure3_readiness_gates.svg)

## Writer-facing companion documents

- [FINAL_PAPER_HANDOFF.md](/F:/SecureLLM/docs/FINAL_PAPER_HANDOFF.md)
- [PAPER_CLAIM_EVIDENCE_MATRIX.md](/F:/SecureLLM/docs/PAPER_CLAIM_EVIDENCE_MATRIX.md)
- [PAPER_RESULTS_DRAFT.md](/F:/SecureLLM/docs/PAPER_RESULTS_DRAFT.md)
- [PAPER_LIMITATIONS_DRAFT.md](/F:/SecureLLM/docs/PAPER_LIMITATIONS_DRAFT.md)
- [PAPER_TABLE_FIGURE_CAPTIONS.md](/F:/SecureLLM/docs/PAPER_TABLE_FIGURE_CAPTIONS.md)
- [PAPER_ABSTRACT_FACTS.md](/F:/SecureLLM/docs/PAPER_ABSTRACT_FACTS.md)
- [PAPER_TERMINOLOGY_AUDIT.md](/F:/SecureLLM/docs/PAPER_TERMINOLOGY_AUDIT.md)
- [PAPER_CLAIM_RISK_AUDIT.md](/F:/SecureLLM/docs/PAPER_CLAIM_RISK_AUDIT.md)

## Supporting methodology and reproducibility material

Use the reproducibility and protocol documents to explain how results were
created, but do not substitute their prose for the authoritative exact values:

- [PAPER_REPRODUCIBILITY.md](/F:/SecureLLM/docs/PAPER_REPRODUCIBILITY.md)
- [MANUAL_BENCHMARK_AND_LABELING_PROTOCOL.md](/F:/SecureLLM/docs/MANUAL_BENCHMARK_AND_LABELING_PROTOCOL.md)
- [RECONCILIATION.md](/F:/SecureLLM/docs/RECONCILIATION.md)

## Materials not to cite as final scientific evidence

- Raw local-run traces or dashboard screenshots without their associated
  evidence-status record.
- Pre-fix or exploratory experiment outputs.
- Fixture data and test-only artifacts.
- Historical dashboard continuation and local-pipeline audit prose.
- The local three-case pilot as a model comparison.

## Required paper checks before submission

Every numerical calibration statement must match Table 2. Every local-demo
statement must retain the engineering-only qualifier. Every metric-family
statement must retain its readiness status. Remove any sentence that implies
human replacement, ranking, ASR, calibrated risk, predictive performance,
statistical significance, or a general security conclusion.
