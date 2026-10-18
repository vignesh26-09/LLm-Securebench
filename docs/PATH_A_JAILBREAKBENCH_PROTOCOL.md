# Path A: JailbreakBench Validation Protocol

## Research question

How closely do separately specified SecureLLMBench judge decisions agree with the published JailbreakBench human-majority labels on the official judge-comparison set?

## Imported source snapshot

- Source: JailbreakBench `JBB-Behaviors`, `judge_comparison` configuration.
- Immutable revision: `b2b462fd32ca655e0bdfc70b68155720977f4d69`.
- Local source file: `data/external/jailbreakbench_judge_comparison_b2b462fd.csv`.
- Records: 300.
- SHA-256: `dacaf76a1057785f11b0fc6aa07b9a73cdab588319ddfc5e8cef2909e5b112a5`.
- Label fields are retained losslessly in the accompanying manifest. The source has three individual human labels and a `human_majority` label.

## What can be reported now

The source snapshot, hash, schema, label prevalence, and agreement among the source-provided label columns can be described as properties of the imported benchmark. This is not yet a SecureLLMBench calibration result.

## Required decision before calibration execution

The benchmark fields are binary while SecureLLMBench produces continuous `safety_stance` and `instruction_following` measurements. The source metadata available with the import does not state an approved mapping from those concepts to either binary value. Before running Gemma judge calibration, the study must register:

1. Which source field is the reference (`human_majority` is the candidate).
2. The meaning of binary values `0` and `1`, confirmed from the benchmark’s official documentation.
3. Which SecureLLMBench dimension and threshold define a positive prediction.
4. The threshold-selection rule and held-out evaluation split, so labels cannot tune and test the same threshold.
5. The planned statistics: confusion matrix, agreement coefficient with interval, coverage, and error analysis.

Without this decision, a threshold or label direction would be invented after observing the data. The imported labels therefore remain source-native evidence rather than an attack-success rate or a calibration claim.

## Reproducibility controls

The source revision, local-file checksum, installed target/judge models, prompt/rubric versions, generation configuration, threshold-selection split, and any exclusion should be recorded before execution. SecureLLMBench detector output must remain separate from the source human label.
