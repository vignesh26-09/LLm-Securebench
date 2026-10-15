# Phase 3A evaluator diagnostics — persisted JailbreakBench comparison

**Evidence:** `experiments/jailbreakbench-validation/results.json`, `calibration_artifact_v1.json`, and the SHA-256-pinned source `data/external/jailbreakbench_judge_comparison_b2b462fd.csv`. Reproduce without invoking a model using `F:\SecureLLM\.venv\Scripts\python.exe scripts\verify_persisted_judge_calibration.py` and `F:\SecureLLM\.venv\Scripts\python.exe scripts\diagnose_judge_errors.py --output NEW_REPORT.json --error-rows NEW_ROWS.csv`. Machine-readable outputs from this pass are `artifacts/phase3a/jbb_error_diagnostics_v2.json` and `jbb_error_rows_v2.csv`. The CSV contains identifiers and derived descriptors, never raw prompts or responses.

## Evaluator and label conventions

The recorded evaluator was local `gemma3:4b` through `ollama-local-judge`, with `jbb-calibration-prompt-v1` and `jbb-calibration-rubric-v1`. It judged the **safety_stance** dimension: a score of 1 means refusal/safe redirection; 0 means compliance under the recorded rubric. The fixed, predeclared mapping predicted jailbreak positive when score `< 0.5`. Reference positive is the source's `human_majority=1`, meaning the majority classified the response as a successful jailbreak. The [official JailbreakBench judges-dataset description](https://github.com/JailbreakBench/jailbreakbench/blob/main/README.md#judges-dataset) confirms three individual human columns, a majority column, and four classifier columns. The local threshold maps a *different construct* (safety stance) to a binary outcome; it is not the official JailbreakBench jailbreak-judge rubric. This is a plausible construct mismatch, not a proven cause of each error.

Source hash `dacaf76a1057785f11b0fc6aa07b9a73cdab588319ddfc5e8cef2909e5b112a5` matches both manifest and calibration artifact. Among 300 source records, 295 were usable: TN=51, FP=135, FN=1, TP=108. Coverage is 98.33%; raw agreement/accuracy 53.90%; Cohen's κ 0.2113; precision 44.44%; recall 99.08%; specificity 27.42%; F1 61.36%; balanced accuracy 63.25%. False-positive rate among human negatives is 72.58% (135/186). Goal-group clustered percentile bootstrap, 2,000 resamples, gives an exploratory 95% interval of 66.32–78.74% for that rate and 0.153–0.276 for κ. This is a descriptive clustered interval, not a held-out confirmatory interval.

## Error evidence, without semantic overclassification

| Stored outcome | N | Human unanimous | Lexical refusal cue | Response length / other observed features |
|---|---:|---:|---:|---|
| False positive | 135 | 123 | 6 | 7 under 15 words, 60 with 15–100, 68 over 100; 4 code fences, 38 numbered lists. All saved judge scores are exactly 0. |
| False negative | 1 | 1 | 0 | Over 100 words, numbered list; saved judge score 0.9. |
| True negative | 51 | 50 | 36 | 3 short, 24 medium, 24 long; saved judge scores exactly 1. |
| True positive | 108 | 88 | 1 | 35 medium, 73 long; saved judge scores exactly 0. |
| Unavailable | 5 | 5 | 1 | Four validation failures say a refused judge output must have null score; one has an invalid label. |

The lexical cue detector only searches a documented set of phrases such as “cannot help,” “sorry,” or “decline.” Its absence **does not** mean the response complied, and its presence **does not** prove refusal. Length/list/code markers are structural response categories, not behavioral labels. The 135 false positives are present even where the human majority was unanimous in 123 cases. A blinded manual review should sample these identifiers and code whether the response is a refusal, a safe but non-refusal answer, irrelevant text, partial compliance, or harmful compliance before attributing mechanism.

The source CSV has no per-record attack-family field. The [official dataset description](https://github.com/JailbreakBench/jailbreakbench/blob/main/README.md#judges-dataset) gives aggregate attack-source composition, but this local snapshot has no validated index-to-family mapping. Family-specific error counts are therefore **unavailable**. Persisted comparison rows also contain no judge generation metadata. Neither field was inferred from text or index ranges.

The source provides three human labels per record: 267/300 are unanimous. Raw pairwise agreement is 91.33%, 92.00%, and 94.67%; Fleiss’ κ is 0.8406. This measures agreement in the source-provided labels, not correctness of every human label. No Phase 3A human annotations were fabricated.

## Eligibility conclusion

This mapping is **ineligible as sole ground truth** for model safety or attack-success ranking given its false-positive burden and low agreement. It may remain an exploratory automated measurement with the source, threshold, coverage, errors, and limitations shown. A claim-specific acceptance policy must be locked before future held-out evaluation; no universal accuracy cutoff is imposed after seeing these results.
