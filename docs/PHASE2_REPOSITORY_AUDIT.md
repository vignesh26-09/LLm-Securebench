# SecureLLMBench Phase 2 repository audit

**Audit date:** 10 October 2026. **Baseline:** 167 Python tests passed, one upstream TestClient deprecation warning. The project interpreter is `F:\SecureLLM\.venv\Scripts\python.exe`; sandboxed launches failed, while the same interpreter passed the suite with approved execution. Coverage percentage has not been measured.

## Verified implementation and data flow

| Area | Verified current behavior | Boundary or gap |
|---|---|---|
| Demonstration execution | `apps/api/local_execution.py` discovers installed Ollama models, accepts a loopback-only job, tracks progress in memory, and calls `scripts/run_local_benchmark.py`. Remote OpenAI-compatible execution is operator-enabled. | Job state disappears on server restart. API job input selects a model, not an arbitrary research dataset. |
| Demonstration dataset and inference | `run_local_benchmark.py` hashes and imports `data/raw/example.json`, runs its three records with `BenchmarkEngine`, and stores JSON plus SQLAlchemy rows. Providers preserve failures, latency, token counts when available, and model settings. | Three cases are engineering evidence. No automatic model download. |
| Demonstration measurements | Three fixed Layer 1 rules yield detector-native observations. DRAA and PRI profiles, latency statistics, and an `engineering_only` model-score record are persisted. | Detector scores do not establish attack success or safety. Layer 2 and independent human labels are not run automatically in this path. |
| Controlled research runner | Strict versioned specification, installed Ollama identity check, baseline, independent isolated attack, genuine ordered sequence, recovery probes, immutable observation JSON, resumability, control identity, canary and contamination records, and reproducibility manifest. | `scripts/run_controlled_experiment.py` runs target inference and persists observations; it does not automatically invoke a validated behavioral measurement or independent human outcome workflow. Locked preregistration is optional in the runner and not required by this CLI. |
| Context evidence | Ollama records complete sent history and context-window/token metadata; canary gives probabilistic request-level evidence. Suspected shared-session contamination blocks SAEA isolated deltas. | Missing provider evidence remains unknown. A canary cannot prove full context retention. |
| Persistence | SQLite-compatible SQLAlchemy entities include dataset/version, model configuration, run, evaluation, Layer 1/2 result, append-only scientific record, and review. Duplicate scientific IDs are rejected. | Dataset/measurement metadata are stored as JSON; cross-record scientific eligibility is enforced by application rules, not relational foreign keys. |
| Read API and charts | `/scientific-records`, `/research-evidence/{family}`, resource lists, run reports, and `/reports/charts/{chart_type}` expose records. Charts require `real_persisted` plus `phase1_scientific` or `external_calibration` provenance and never draw an empty chart. | Only the real stored judge calibration currently qualifies for a paper chart. The API is not a complete study authoring/annotation interface. |

## Existing metric definitions and status

- **ASR:** `core/evaluation/attack_outcome.py` counts `success=True` only among `classified` outcomes; ambiguous, failed, skipped, unavailable, and not-applicable records are excluded with counts. This is a contract, not a validated local ASR result.
- **BSDA:** `core/metrics/bsda.py` computes semantic, safety, instruction, and structural components from pre-generated matched inputs. Calibration and missing representation states are explicit. No qualifying Phase 1 component distribution exists.
- **RC:** `core/recovery/engine.py` uses safety/helpfulness behavioral states and normalized Euclidean distance; raw AUC and terminal recovery require a compatible external applicability calibration. Otherwise the score is null with a reason.
- **SAEA:** `core/saea/engine.py` consumes a baseline, genuine sequential states, and matched isolated controls. Per-step context effects are blocked for incompatible identities or suspected contamination; this is not ASR.
- **DRAA/PRI:** implemented evidence/profile transport; scalar risk and PRI scores are null by design.
- **DQI/ML/statistics:** exploratory DQI preserves missing semantic inputs; ML infrastructure requires independent labels and leakage-reviewed splits; statistical utilities exist but no production model-comparison inference is established.
- **Local `model_score`:** average absence of three heuristic detector signals among completed three-case evaluations, explicitly `engineering_only`, not a safety grade.

## Evaluator and annotation interfaces

`core/judging/service.py` validates a dimension-specific structured judge response, including score/label/confidence and evidence citations; malformed or mismatched dimensions fail or retry. The local Ollama judge adapter and mock provider exist. `core/evaluation/human_validation.py` has blinded-sample and agreement primitives, but the export retains a join ID in the same object and there is no complete two-rater, adjudicated, versioned import workflow. `core/evaluation/judge_calibration.py` computes confusion counts, agreement, kappa, precision, recall, F1, bootstrap intervals, and attack-family strata. Specificity, balanced accuracy, split enforcement, and a multiclass outcome evaluator are not yet present.

The existing JailbreakBench calibration artifact is real: 300 source records, 295 usable, 98.33% coverage, 53.90% raw agreement, Cohen's kappa 0.211. Under the fixed mapping, this judge cannot replace independent human labels. This is an exploratory negative calibration result, not a validated target-model comparison.

## Reproducibility, security, and data-handling risks

1. A declared dataset hash in the controlled specification is retained but the CLI does not independently re-read a source dataset and verify its bytes. The specification embeds cases; a study must maintain its versioned source manifest separately.
2. The controlled CLI does not enforce a locked preregistration by default. Scientific use requires an explicit policy gate or a documented external check before execution.
3. The target runner records responses but no automatic measurement bridge supplies behavioral states. Treat any missing BSDA/RC/SAEA result as unavailable rather than deriving labels from detector counts.
4. The demonstration job registry is in memory and one job runs at a time. Operational failures are persisted as evaluations where the runner reaches storage; a process crash before persistence can leave only partial JSON or no database record.
5. Annotation exports must omit model identity and raw database IDs from rater-facing files, separate the join map, and avoid claiming automatic removal of sensitive text. Human review is required before distributing prompts or responses.
6. Remote inference is disabled unless opted in; request credentials are excluded from persisted configuration. Loopback and origin restrictions protect the local execution API, but are not a general multi-user authentication system.
7. Scientific records may contain harmful prompt/response text. Repository publication or external sharing requires a separate content and access review; existing redaction primarily covers configuration credentials.

## Prioritized Phase 2 backlog

1. Build a two-rater blinded annotation export/import and adjudication workflow with strict schemas, separate join mapping, immutable versioned records, and genuine human provenance.
2. Add an outcome-specific automated evaluator contract and parsing without reinterpreting the existing dimension judge. Extend calibration with specificity, balanced accuracy, eligible counts, and split protections; preserve the real JailbreakBench artifact.
3. Add explicit study-readiness checks: locked preregistration, source dataset hash verification, matched benign controls, and measured behavior availability before metric computation.
4. Wire a versioned measurement ingestion stage to the controlled observations; keep Layer 1 signals separate from behavioral ground truth.
5. Implement planned grouped/paired inference and scientific charts only after qualifying real records exist; expose exclusions and uncertainty.
6. Run an independently labeled, repeated multi-model study and compare with ASR and closest published methods. No empirical novelty or model ranking can be claimed until then.

This audit records current code and tests; it does not create scientific data or certify conference readiness.
