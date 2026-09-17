# Backend Controlled-Trajectory Implementation Report

## 1. Executive Summary

This implementation replaces the unsafe legacy assumption that independent prompts establish retained context. SecureLLMBench now has a controlled, versioned trajectory protocol: complete ordered conversations, immutable condition observations, matched isolated controls, explicit context evidence, reproducibility manifests, versioned outcome/calibration artifacts, and paired-analysis primitives. Existing BSDA, RC, and SAEA equations were not changed.

The implementation does not fabricate scientific results. The new runner stores observations and metadata only; behavioral measurements must be supplied by an independently configured measurement stage. A missing measurement remains failed/unavailable and cannot become a numeric RC or SAEA value.

## 2. Files Added

- `core/experiments/models.py`, `runner.py`, `trajectory.py`, `specification.py`, `manifest.py`, and `persistence.py`: controlled experiment contracts, append-only JSON/SQL evidence, metric-input bridge, and manifest support.
- `core/evaluation/judge_calibration.py`: versioned calibration artifact calculation.
- `core/statistics/paired.py` and `complementarity.py`: paired descriptive/effect/CI analysis and raw exploratory complementarity tables.
- `scripts/run_controlled_experiment.py`: safe CLI for already installed local Ollama models.
- `scripts/build_judge_calibration_artifact.py`: recomputes an artifact from stored source/results evidence.
- `experiments/jailbreakbench-validation/calibration_artifact_v1.json`: actual persisted calibration artifact.
- `tests/test_research_protocol.py`: controlled-protocol invariants.

## 3. Files Modified

Inference contracts/providers, the benchmark engine, DQI, SAEA, outcome evaluation, existing scripts, the legacy paper runner, and their tests were updated. No frontend files or metric equations were modified.

## 4. Stateful Conversation Architecture

`ConversationRequest`, `ConversationMessage`, and `ConversationResponse` preserve session ID, ordered messages, turn IDs, model identity/digest, generation configuration, seed evidence, token usage when exposed, and context evidence.

Ollama uses `/api/chat` with the complete constructed history. `RETAINED` requires complete ordered history plus provider prompt-token evidence within a declared model context window. Missing window/token evidence is `UNKNOWN`; an over-window prompt is `TRUNCATED`. OpenAI-compatible providers preserve the complete request but return `UNKNOWN` unless the provider exposes truncation evidence. The deterministic mock provider provides retained fixture evidence only.

## 5. Experimental Condition Architecture

`ExperimentSpecification` defines versioned dataset identity/hash, models, cases, attacks, sequences, recovery probes, generation settings, seeds, repetitions, and measurement configuration. `ExperimentRunner` creates baseline, one isolated `B → A_i` session per attack, a genuine `B → A_1 → … → A_n` session, and recovery turns on that attacked conversation.

Each immutable `ExperimentalObservation` contains condition, case/dataset, attack identity/family, sequence identity/position, provider/model/version, requested/effective seed, configuration versions, timestamp, full message history, context status/reason, and provider metadata. Observation IDs are deterministic; completed or failed observations are not rerun on resume.

## 6. Matched-Control Enforcement

`ControlMatchIdentity` records case, attack and instance identity, model/digest, provider, generation digest, dataset version, behavioral representation, Layer 1/Layer 2 versions, measurement version, and threat model. `validate_control_match` rejects each mismatching field with a precise reason. `SAEAEngine` returns an undefined per-step context effect instead of computing one when supplied identities disagree.

Legacy SAEA callers with no identities remain supported for backward compatibility, but the controlled runner always emits identities. A one-sided missing identity is rejected.

## 7. Recovery Protocol

Recovery probes are generated after the actual sequence attack in the same conversation. `build_recovery_input` converts controlled observations plus explicitly supplied behavioral measurements into `RecoveryRunInput`, including session, generation, source, and context provenance. RC remains blocked if context is unknown/truncated, if behavior measurements are absent, or if `Delta_A` is at/below its calibrated applicability floor.

## 8. SAEA Protocol

`build_saea_input` selects the sequence baseline, each genuine sequential position, and that attack's separate isolated `B → A_i` control. It does not reuse an isolated state across positions. It transfers the matching identity into `AttackInstance`; missing controls/measurements remain null/undefined. The existing normalized distance and `Delta_i − V_iso(A_i)` equations remain unchanged.

## 9. Attack Outcome / ASR Pipeline

`AttackOutcomeRecord` now retains threat model, label source/version, outcome version, timestamp, evaluator identity/version, reason, evidence, and provenance. `import_human_outcomes` imports JSON/CSV independent human labels without deriving labels from Layer 1/Layer 2. `calculate_asr` still uses only classified records in its denominator; ambiguous, failed, skipped, unavailable, and not-applicable records stay excluded.

## 10. Judge Calibration Pipeline

`JudgeCalibrationArtifact` retains dataset revision/hash, source/usable N, coverage, judge/model/digest when available, prompt/rubric versions, mapping, human source, agreement, kappa, confusion matrix, precision/recall/F1, bootstrap intervals, strata, software version, and provenance.

The generated JailbreakBench artifact recomputes from the persisted CSV/results: N=300, usable N=295, coverage=98.333%, agreement=53.898%, κ=0.211261, TN=51/FP=135/FN=1/TP=108. Its status remains `not_validated`; the original result did not retain a judge digest, and that absence is explicit.

## 11. Statistical Analysis

`paired_difference_analysis` accepts only complete pre-matched pairs, records exclusions/missingness, reports mean paired differences, paired standardized effect size when defined, and deterministic percentile bootstrap intervals. It returns `unsupported` when no complete pairs and `insufficient_data` when uncertainty is not estimable. `grouped_paired_analyses` supports model, family, condition, or another caller-defined grouping key.

## 12. Complementarity Analysis

`complementarity_table` preserves raw paired ASR/trajectory values. Thresholds are optional and explicitly marked exploratory; the component does not choose a scientific threshold or force a complementarity conclusion.

## 13. Reproducibility Manifest

Every controlled CLI run produces `manifest.json` containing experiment identity, git commit/dirty status, dataset identity/hash, model identity/digest, provider, generation and seed evidence, configurations/versions, runtime versions, platform, start/end, counts, artifact SHA-256 hashes, and explicit unavailable reasons. The manifest never invents unavailable values.

## 14. DQI Missingness Correction

When semantic embeddings are absent, DQI novelty is now `null` and DQI composite score is `null` with status `unavailable` and reason `semantic_embeddings_unavailable`. The old zero substitution is removed. Existing repository DQI import/endpoint and smoke tests now preserve that state.

## 15. Seed/Reproducibility Correction

`BenchmarkConfig.seed` is passed to `InferenceRequest`. Providers record requested/effective seeds and whether deterministic seeding is supported. Ollama transmits its effective seed; the OpenAI-compatible adapter transmits it only when explicitly configured as supported; fixture providers provide deterministic support evidence.

## 16. Persistence Changes

The existing append-only `scientific_records` table is used without schema migration because it already stores versioned family, scope, status, payload, and provenance. `append_scientific_artifact` refuses duplicate record IDs. The controlled CLI persists specification, observations, control identities, and reproducibility manifest. The adapter also supports outcomes, calibration artifacts, BSDA, RC, SAEA, paired analyses, and complementarity artifacts.

## 17. Tests Added

The new suite verifies complete sequential history; independent isolated history; recovery history; retained/unknown context handling; deterministic resume; failed-observation persistence; seed delivery; every control-match mismatch; SAEA rejection; explicit ASR exclusions; calibration metrics/coverage; DQI null missingness; append-only persistence; manifest unavailable reasons; paired analysis; complementarity labeling; and controlled-observation conversion into RC/SAEA inputs.

## 18. Test Results

Baseline: 138 passed. Final suite: 151 passed, 0 failed, 0 skipped. Collection: 151 tests. Focused protocol suite: 43 passed before final additions; focused paper/protocol/regression suite: 36 passed after legacy-runner correction. The deterministic end-to-end smoke completed and correctly reported DQI as unavailable without embeddings. Coverage was not run because `pytest-cov` is not installed; no dependency was installed.

## 19. Real-Provider Smoke-Test Status

Ollama service check succeeded (`0.34.1`) and local Qwen/Gemma registrations were discovered. Two harmless Qwen generation attempts produced no usable response before the execution window, so real-provider generation smoke is `UNAVAILABLE/TIMEOUT`. No experimental result was persisted or interpreted from those attempts.

## 20. Remaining Scientific Limitations

The JudgeCalibrationArtifact documents weak agreement and is not a validation artifact. No independent production human-label cohort has yet been imported. The controlled runner records target responses but does not automatically promote Layer 1 or Layer 2 output into behavioral states. No production multi-case/multi-model repeated experiment has been run. Bootstrap intervals are exploratory and rely on the stated record-level IID assumption.

## 21. Remaining Work Before Real Experiment

Prepare a versioned experiment specification, verify responsive local provider operation, lock Layer 1/Layer 2 configurations, collect independent human attack outcomes, create a stronger judge calibration artifact if applicable, run a preregistered repeated multi-case study, then persist measured BSDA/RC/SAEA and paired analyses through the artifact adapter.

## 22. Claim-Safety Matrix

| Capability | Implemented | Runtime Wired | Tested | Real-Model Smoke | Calibrated | Real Experimental Validation | Claim Safe |
|---|---|---|---|---|---|---|---|
| Stateful execution | Yes | Controlled CLI | Yes | Unavailable/timeout | N/A | No | Engineering protocol only |
| Matched controls | Yes | Controlled CLI + SAEA guard | Yes | No | N/A | No | Engineering protocol only |
| BSDA | Existing formula preserved | Artifact adapter | Existing + guarded inputs | No | No | No | Formula/guard only |
| Recovery | Existing formula preserved | Controlled-input bridge | Yes | No | No | No | Formula/guard only |
| SAEA | Existing formula preserved | Controlled-input bridge | Yes | No | No | No | Formula/guard only |
| ASR | Yes | Human import + artifact adapter | Yes | No labels imported | N/A | No | Definition/pipeline only |
| Judge calibration | Yes | Artifact builder | Yes | Existing persisted comparison | No | Exploratory negative result | Low-agreement result only |
| Statistics | Paired subset | Artifact adapter | Yes | N/A | N/A | No | Descriptive/exploratory only |
| Complementarity | Raw/exploratory table | Artifact adapter | Yes | N/A | N/A | No | Infrastructure only |
| Reproducibility | Yes | Controlled CLI | Yes | No completed run | N/A | No | Engineering protocol only |
