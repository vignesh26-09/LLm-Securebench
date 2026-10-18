# Layer 1 fast detection

## Scope and status

Layer 1 emits configurable, fast heuristic signals from text. It currently
implements deterministic regex, keyword, and token-pattern detectors plus an
aggregation layer. Its results are **signals, not ground truth**, and neither an
individual detector nor an aggregate score is scientifically validated.

No Layer 2 semantic judging, human labeling, BSDA, SAEA, DRAA, PRI, ML
prediction, dashboard, or new benchmark orchestration is implemented here.

## Detector contract

Every detector returns `DetectorResult` with a detector name, score, optional
confidence, matched evidence, per-signal scores, and metadata. Scores range from
0 to 1. The current signal names are `injection`, `leakage`, and `jailbreak`.
Rules and their scores are caller-provided; SecureLLMBench does not supply a
universal policy or claim a universal taxonomy.

`SemanticSimilarityDetector` and `ToxicityDetector` are interfaces only. No
semantic-similarity or toxicity detection implementation is present in Layer 1.

## Aggregation and severity

`LayerOneAggregator` takes the maximum score from all detectors for each signal
and applies caller-configured signal weights to form a weighted mean aggregate.
`SeverityThresholds` maps that aggregate to `none`, `low`, `medium`, `high`, or
`critical` using configurable boundaries.

Attack success is intentionally not defined universally. It is `None` unless a
caller supplies an `AttackSuccessRule`. `ThresholdAttackSuccessRule` is one
configurable policy option, not a definition of successful attack behavior.

## Limitations

Regexes, keywords, and term patterns can generate false positives when benign
discussion, quotation, documentation, negation, or incident reporting contains
configured terms. They can generate false negatives for paraphrases, multilingual
forms, encoded text, novel phrasing, context-dependent behavior, and attacks that
do not use configured terms. Rule scores, thresholds, severity, and aggregation
weights need task-specific calibration and ground-truth evaluation before they
support any research claim.
