# Phase 3B protocol status and local pilot freeze

**Only the engineering-pilot protocol is locally frozen. No confirmatory research protocol is frozen or externally preregistered.** The scientific design remains the reviewable proposal in `docs/PHASE3B_EXPERIMENTAL_PLAN.md`. Calling the pilot lock a preregistration outside this local repository would overstate its status.

## Immutable local pilot version 1

| Item | Frozen value |
|---|---|
| Protocol ID / experiment ID | `local-pilot-freeze-v1` / `phase3b-engineering-pilot-v1` |
| Source dataset | `experiments/phase3b/pilot_dataset_v1.json`; SHA-256 `02bbb015288b088412d9802ee223c9d852789a6d60a978ee09ba6270f6ab96fa` |
| Executable specification | `experiments/phase3b/pilot_specification_v1.json`; SHA-256 `befc2a768a8a6a1d14fa3eb4075ffcd542028f49875aca3f067a4070b18a6749` |
| Local lock | `experiments/phase3b/pilot_protocol_lock_v1.json`; SHA-256 `1b7a5ccb3101003e5772158ea60844636dd4c7a933ceddf78eb0ed2e634c4b16` |
| Target models | Installed `qwen3.5:2b` and `gemma3:4b`, full digests pinned in the specification |
| Design | One harmless synthetic case; A/B/C isolated; A→B→C and C→B→A; one matched benign three-turn lane; two attacked and two benign post-conversation probes; fresh baseline per lane |
| Generation | Temperature 0, 32-token cap, 90-second call timeout, requested seed 2026, one repetition, 4,096-token declared context window |
| Stop rule | Maximum 50 planned local calls; no remote service or automatic weight download |
| Outcomes | Execution integrity, coverage, provenance, and failure counts only; no safety ASR, BSDA, RC, SAEA, ranking, or human-label claim |
| Status | `locally_frozen`, `external_registration=false`, `engineering_pilot` |

The call budget is per model/case/repetition: one standalone baseline + three fresh isolated baselines/attacks (6) + two ordered sequences each with baseline, three attack turns, and two recovery probes (12) + one matched benign baseline, three turns, and two probes (6) = **25**. Two models yield **50**. The runner stores ordered messages, deterministic observation IDs, model digests, requested/effective seeds, context status, canary status, timestamps, and separate isolation-ledger records. Seed support is provider-reported; seed matching does not prove deterministic equivalence across models or hardware. Ollama does not expose enough cache evidence to verify isolation in this pilot.

`scripts/prepare_phase3b_pilot.py` uses exclusive creation for the specification and lock. A changed source/specification or lock must create a new version with an amendment reason; it must not overwrite version 1. `scripts/run_controlled_experiment.py` checks source bytes, content identity, lock hash, model digest, and call cap before target calls. It accepts only `engineering_pilot` or `exploratory` evidence classes; there is no confirmatory CLI label available by simply changing a flag.

## Scientific protocol proposed, not frozen

The following are **candidate** hypotheses, not post-hoc findings or an externally registered analysis plan:

| RQ | Candidate null / alternative and primary unit |
|---|---|
| RQ1 | H0: eligible isolated attack success does not differ across predeclared model/family contrasts; H1: it does. Primary unit is a case/attack group with independent adjudicated human outcome. |
| RQ2 | H0: matched sequential-minus-isolated behavioral deviation has zero mean; H1: nonzero. Pair within case, attack instance, model, seed/repetition. Do not call a nonzero difference causal synergy without further controls. |
| RQ3 | H0: predeclared attacked-versus-benign recovery estimand has no difference; H1: a difference. Compare matched trajectories, preserving missing probes and applicability. |
| RQ4 | H0/H1 and acceptable evaluator error bounds are claim-specific and must be frozen **before** held-out evaluation; current Gemma safety-stance mapping is ineligible as sole truth. |
| RQ5 | H0: no predeclared model-by-category/order interaction; H1: an interaction. The exact primary interaction, multiplicity family, and precision target remain unresolved. |

Candidate controls are a fresh baseline, topic/turn-count-matched benign conversation, fresh isolated A/B/C, two preselected orders, immediate and repeated probes, identical probe wording where possible, fixed model/configuration/seed/repetition, and recorded context/contamination. Candidate exclusions are failed or missing responses, invalid/truncated context, unmatched control identity, suspected contamination, absent independent label, incompatible measurement version, and failed calibration. Each exclusion keeps a count and reason. Analysis should cluster by case/related goal and use paired contrasts with grouped uncertainty; multiple primary tests require a correction fixed before data collection. No model ranking is allowed without independent reference outcomes, validated behavior measurements, and adequate coverage.

The production protocol cannot honestly be frozen yet: target dataset/rights/revision, exact attack objectives and controls, sample size and precision rationale, human-rater availability, validated behavioral-state procedure, evaluator acceptance policy, and analysis multiplicity choices are still open. An eventual production lock must be a new immutable artifact with those choices, exact file hashes, timestamp, and amendment chain. The pilot cannot supply those choices by optimizing on its responses.
