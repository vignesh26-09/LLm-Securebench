# Results summary for the paper and viva

## Setup
1. Three local models: gemma3:4b, qwen3.5:2b and llama3.2:3b; no larger-model claim.
2. Original pilot: 50 prompts per model, with separate LLM annotation checks [P,L].
3. Synthetic canary evaluation: 180 outputs; the retrospective test subset has 90 outputs, including 35 objective positives [J].
4. One human labeler checked 30 selected outputs; objective calibration used 180 model-question pairs and 360 canary generations [H,A].
5. Temperature was 0 with fixed recorded seeds; objective calibration and paired bootstrap use seed 42 and 1,000 resamples [A].

## Artifact key
- [A] `data/calibration/objective_summary_recomputed.json` (tracked aggregates; includes `paired_ml_differences`).
- [J] `experiments/local-runs/canary-devtest/devtest-20261018-042016/test_metrics.json`.
- [O] `experiments/local-runs/oracle-sanity/oracle-20261018-043342/sanity_summary.json`.
- [P] `experiments/local-runs/controlled/verification-20261017-232316/state.json`.
- [L] `experiments/local-runs/controlled/verification-20261017-232316/labeling/sample2_metrics.json`.
- [H] `experiments/local-runs/controlled/verification-20261017-232316/labeling/human_kit/human_validation_report.md`, with `human_sheet.csv` and `human_key.csv` in the same folder.
- [D] `docs/metrics_calibration.md`; [C] `docs/COMPONENT_VALIDATION_PHASE10D_FORMAL_SPEC.md`.

Raw run folders are local and are NOT included in the published repository.

## Evidence table
Strength applies only to the stated narrow claim; it is not a calibration status. Intervals are 95%; percentages are rounded.

| Claim | Evidence type | Key numbers and intervals | Strength |
|---|---|---|---|
| V0 misses most known canary emissions | objective canary | Recall 2/35 = 5.71% [1.58%,18.61%]; false-alarm rate 0/55 = 0% [0%,6.53%], Wilson [J,A] | moderate |
| V3 exchanges higher recall for many false alarms | objective canary | Recall 28/35 = 80% [64.11%,89.96%]; false-alarm rate 25/55 = 45.45% [33.03%,58.48%], Wilson [J,A] | moderate |
| Historical oracle accuracy is not independently measured | descriptive | 73/180 fired, **by construction**, no accuracy CI; this historical run used a broader fragment rule [O] | not estimable |
| Agreement between LLM references is not factual truth | LLM-annotated | Sample 2: n=60, judge/reference agreement 91.67%, kappa .2481; non-safe recall 1/4 = 25% [L] | weak |
| LLM reference agreement with the single human check is limited | human n=30 | 23/30 = 76.67% [59.07%,88.21%], conditional Wilson CI [H,A] | weak |
| The human sample cannot estimate non-safe recall | human n=30 | Safe=30, unsafe=0, borderline=0; judge agreement 90%, kappa 0, AC1 .8950; non-safe recall and its CI unavailable [H] | not estimable |
| Factual-answer lift is not identified by near-total abstention | descriptive | Ungrounded abstention 100% for all models. Primary complete pairs Gemma/Qwen/Llama=0/44/39; Gemma lift unavailable, other raw contrasts 0 [0,0] [A] | not estimable |
| Strict extraction accounts for many missing QA pairs | descriptive | Primary format failures=97. Separate post-hoc sensitivity=9 failures and 53/60/58 pairs; the primary extractor was NOT changed post hoc [A] | moderate |
| Prompt-only logistic AP exceeds majority on these template holdouts | objective canary | AP .4894 vs .3013; paired difference +.1881 [.0667,.3118], zero excluded, 12 template groups [A] | moderate |
| Model-transfer AP improvement is fragile | objective canary | AP .3978 vs .3448; paired difference +.0530 [.0240,.1666], zero excluded, only 3 model groups [A] | weak |

Both V0 and V3 received original system context; missing context is not an explanation for V0's misses (`scripts/run_canary_evaluation.py`, `scripts/judge_devtest.py`).
The context proxy is grounded versus ungrounded fictional QA, NOT canonical adversarial-minus-matched-benign MCHL. Grounded abstention among scorable responses is unavailable/22.73%/2.56% for Gemma/Qwen/Llama; all ungrounded rates are 100% [A].
Primary scoring failures remain failures. Seven canary generations remain failed after output-cap-only regeneration (37 before); ML uses 353 completed cases, including 147 oracle positives [A].

## Paired ML interval provenance
Every new paired CI is **recomputed from stored features/labels, not stored predictions**, using `scripts/summarize_paired_ml.py` [A].
The authorized CPU-only reconstruction reproduced all four stored APs exactly (tolerance .005), with unchanged features, folds and logistic settings. New OOF scores are local, outside old runs.
The sole stored model is logistic regression; model-versus-majority and logistic-versus-majority are the same comparison, not two independent findings.
Template CIs resample 12 template groups; model-transfer CIs resample 3 model groups, paired across estimators, seed 42, 1,000 resamples; undefined replicates=0 for both.
Old CIs remain unchanged in `prediction`: both originally resampled template clusters. The old model-transfer difference CI [-.0442,.1980] includes zero; the new model-group CI has a DIFFERENT uncertainty unit, not stronger generalization evidence [A].
These are fixed-prediction bootstrap intervals. They omit training uncertainty; three model groups cannot support reliable population-level transfer claims.

## Claims the evidence supports
- The platform records source provenance, failures and separate evidence types.
- Within the synthetic canary cases, V0 recall is poor and V3 has many false alarms.
- Known-value matching can identify specified emissions; failure to match is not safety.
- Prompt-only logistic scores show limited task-specific AP improvement under the stated folds and uncertainty units.

## Claims the evidence does NOT support
- No validated judge, human-equivalent annotator or general safety classifier.
- No Established scientific calibration, production-selection recommendation or model safety ranking.
- No generalization beyond these three small local models and these synthetic tasks.
- No factual-hallucination effect from 100% ungrounded abstention, nor canonical MCHL from this proxy.
- No causal improvement or robust population transfer claim from these bootstrap intervals.

## Limitations
Models are 2B-4B; samples and positive counts are small. Synthetic canaries cover specified leak/injection only. V3's split was retrospective with earlier evidence inspected. The human check has one labeler, enriched selection and zero non-safe references. Strict answer formatting excludes otherwise plausible answers; sensitivity is post-hoc and separate. Partial oracle matching can yield false positives. Failed generations, correlated prompts and adaptive output-cap retries restrict interpretation [A,D,H,J,O].

## Data needed for calibration of each page
- Scientific reviews: approved scoped claim/evidence bundle, independent decision and review protocol [D,C:69].
- BSDA: independent component references, benign/perturbed controls, frozen bounds and replication [D,C:21-23].
- Recovery: compatible external positive applicability floor, validated state/probe trajectories and controls [D].
- SAEA: isolated/sequential matched controls, order/context/provider-isolation study and versioned plan [D].
- DRAA: independently audited Mode A/B fidelity/provenance/missingness; no scalar estimator is approved [D,C:33].
- PRI: reference coverage, profile compatibility/composition study; scalar/ranking remains unavailable [D,C:35].
- DQI: measured embeddings, independent quality targets, external validity, sensitivity and ablation [D,C:11-13].
- Hallucination lift: canonical adversarial/benign matched factual pairs, frozen references and independent factual-label audit [D].
- ML prediction: independent target study with grouped/temporal holdouts, calibration, replication and claim review beyond this synthetic target [D,C:37].
- Statistics: frozen estimand/design/missingness plan, dependence-aware inference and reviewed scoped replication [D].

## Reproduction paths
- Pilot and labels: `scripts/run_verification_pilot.py`; `scripts/compute_agreement.py`; `scripts/score_human_labels.py`; [P,L,H].
- Canary judges: `scripts/run_canary_evaluation.py`; `scripts/judge_devtest.py`; `experiments/local-runs/canary/canary-20261018-035526/`; [J].
- Historical oracle: `scripts/oracle_sanity.py`; [O].
- Objective primary/retry aggregates: `scripts/run_objective_calibration.py`; `experiments/local-runs/calibration/20261019-150350/`; [A].
- Paired differences and Wilson intervals: `scripts/summarize_paired_ml.py`; [A] `paired_ml_differences`.
