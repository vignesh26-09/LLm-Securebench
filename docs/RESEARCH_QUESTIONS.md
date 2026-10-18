# Research questions and evidence boundaries

The target study asks five questions, not five predetermined conclusions.

| Question | Primary observation | What remains required |
|---|---|---|
| RQ1: isolated attack robustness | Independently human-classified attack outcomes and ASR, stratified by attack family | A sampled, versioned dataset and held-out labels; detector hits are insufficient. |
| RQ2: sequential attack effects | Paired sequential versus isolated observations under matched model, attack, settings, and measurement versions | Verified independent sessions, context evidence, repetitions, and a measured behavioral state. |
| RQ3: recovery capability | Ordered post-attack states relative to a matched baseline | External calibration, benign conversation controls, and interpretable probe design. |
| RQ4: evaluator reliability | Independent rater labels versus automated outcomes, confusion matrix and error analysis | Two-rater annotation, adjudication, separate development/validation/test groups. Existing JailbreakBench agreement is low. |
| RQ5: comparison stability | Model-by-family paired effects across evaluator, seed, and design variations | Multiple installed models and repeated, independently labeled runs; uncertainty analysis. |

The three-case local benchmark supports engineering smoke checks only. The existing JailbreakBench judge comparison is an empirical evaluator-calibration result; it does not answer RQ1–RQ3 or rank target models.
