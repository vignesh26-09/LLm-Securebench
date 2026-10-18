# Paper Writer Inputs

## Authoritative evidence package

Use these files as the source of record for numerical statements and evidence
status:

1. [PAPER_EVIDENCE_MANIFEST.md](/<LOCAL_PATH>)
2. [PAPER_FREEZE_REPORT.md](/<LOCAL_PATH>)
3. [table1_components.csv](/<LOCAL_PATH>)
4. [table2_jbb_calibration.csv](/<LOCAL_PATH>)
5. [table3_local_engineering.csv](/<LOCAL_PATH>)
6. [table_data.json](/<LOCAL_PATH>)
7. [calibration_verification.json](/<LOCAL_PATH>)
8. [figure1_architecture.svg](/<LOCAL_PATH>)
9. [figure2_judge_human_confusion.svg](/<LOCAL_PATH>)
10. [figure3_readiness_gates.svg](/<LOCAL_PATH>)

## Writer-facing companion documents

- [FINAL_PAPER_HANDOFF.md](/<LOCAL_PATH>)
- [PAPER_CLAIM_EVIDENCE_MATRIX.md](/<LOCAL_PATH>)
- [PAPER_RESULTS_DRAFT.md](/<LOCAL_PATH>)
- [PAPER_LIMITATIONS_DRAFT.md](/<LOCAL_PATH>)
- [PAPER_TABLE_FIGURE_CAPTIONS.md](/<LOCAL_PATH>)
- [PAPER_ABSTRACT_FACTS.md](/<LOCAL_PATH>)
- [PAPER_TERMINOLOGY_AUDIT.md](/<LOCAL_PATH>)
- [PAPER_CLAIM_RISK_AUDIT.md](/<LOCAL_PATH>)

## Supporting methodology and reproducibility material

Use the reproducibility and protocol documents to explain how results were
created, but do not substitute their prose for the authoritative exact values:

- [PAPER_REPRODUCIBILITY.md](/<LOCAL_PATH>)
- [MANUAL_BENCHMARK_AND_LABELING_PROTOCOL.md](/<LOCAL_PATH>)
- [RECONCILIATION.md](/<LOCAL_PATH>)

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
