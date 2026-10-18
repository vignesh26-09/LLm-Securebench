# Phase 10D component validation framework
## 1. Phase 10D role
Translate claims into governed experiments; computation is not validation.
## 2. Evidence/readiness gates
PLAN: approved claim/estimand/units/protocol; DATA: independent provenanced data; ANALYSIS: design/inference review; REPLICATION: required scope replication; CLAIM REVIEW: explicit human decision. None is a p-value gate.
## 3. Experiment modes
Mode 1 synthetic sanity=engineering only; Mode 2 pilot=variance/protocol learning; Mode 3 preregistered confirmatory=potential evidence; Mode 4 replication/generalization=scope testing.
## 4. Common validation artifact architecture
Future `ComponentValidationPlan`, experiment/dataset/analysis manifests, evidence bundle, and scientific review record reference Phase 10A plan/artifacts.
## 5. DQI scientific claims
DQI is exploratory; claims require independently defined quality/evaluation targets and no circular target derivation.
## 6. DQI experiments
Synthetic duplicate/imbalance/diversity perturbations; external/reference validity; embedding/normalization/composition sensitivity; component ablation. N is TBD BY POWER/PRECISION ANALYSIS.
## 7. Layer 2 claims
Separate repeat-judge reliability, inter-judge consistency, human/reference agreement, criterion validity, and conditional confidence calibration.
## 8. Annotation/reference design
Independent protocol, definitions, adjudication, provenance, blinding where appropriate; consensus is reference only if protocol declares it.
## 9. Layer 2 experiments
Repeat/stability, independent annotated agreement, criterion study, and probability-semantics-gated calibration study. No universal agreement threshold.
## 10. BSDA claims
Each semantic/safety/instruction/structural component is studied independently; no composite.
## 11. BSDA experiments
Benign stability/paraphrase, format/instruction/safety/semantic perturbations, matched baseline/attack, cross-model replication, redundancy/ablation. Pair base cases.
## 12. RC claims
Recovery after meaningful degradation under calibration-artifact applicability; NA is neither success nor failure.
## 13. RC experiments
Trajectory sanity, controlled degradation/intervention, fast/slow/partial/relapse/no recovery, terminal comparison, session stability, truncation sensitivity. Preserve whole sessions.
## 14. SAEA claims
Sequential context, order, CV_obs, candidate SI, length/spacing/composition, stability, and attribution sanity—not causal Shapley.
## 15. SAEA experiments
Require isolated controls, matched/randomized order where designed, sequence/session grouping, and controlled homogeneous/heterogeneous/stacked/spaced conditions.
## 16. DRAA current validation boundary
Only Mode A/B fidelity, provenance, completeness, serialization, missingness, reproducibility; no risk prediction.
## 17. PRI current validation boundary
Only profile fidelity/coverage/provenance/compatibility/missingness/composition sensitivity; no scalar/ranking.
## 18. ML future validation boundary
Requires independent labels, target protocol, grouped/temporal holdouts, baselines, discrimination/calibration/ablation/OOD. Synthetic 9B is not evidence.
## 19. Experimental units
Declare observation, experimental, sampling, resampling, pairing, parent unit; repeated generations are not automatically independent.
## 20. Hierarchy
Use supplied optional hierarchy only; variants/runs/turns/sessions preserve parent relationships.
## 21. Randomization
Record actual assignment/order/randomization provenance; no post-hoc generic shuffle.
## 22. Controls
Controls are experiment-specific: benign/matched/isolated/no-intervention/reference conditions must be declared.
## 23. Effect measures
Use preregistered, interpretable raw/component measures; no universal threshold or scalarization.
## 24. Uncertainty
Method/unit/confidence/count are plan parameters; dependence must be preserved.
## 25. Multiplicity
Declare family/method/error-rate target when relevant; no defaults.
## 26. Missingness
Retain semantic states, counts, reasons, sensitivity plan; no zero filling.
## 27. Sensitivity
Predeclare sensitivity to models, normalization, prompts, weights, calibration, context, composition, or assumptions as relevant.
## 28. Distribution shift
Assess held-out datasets/models/families/time only with appropriate data and stated scope.
## 29. Replication
Specify required cross-model/dataset/attack-family replication before scope claims.
## 30. Negative results
Report null/imprecise/conflicting/failed-replication results; non-significance is not equivalence.
## 31. Experiment matrix
Templates: `dqi-{claim}-{version}`, `layer2-{dimension}-{version}`, `bsda-{component}-{condition}`, `rc-{trajectory}-{condition}`, `saea-{sequence}-{condition}`. Each records question, claim, primary/secondary estimand, units, grouping/pairing, conditions/control, IV/DV/covariates, analysis/effect/uncertainty/multiplicity/missingness/sensitivity/generalization/evidence/blockers; sample size is TBD BY POWER/PRECISION ANALYSIS.
## 32. Validation dataset manifest
Preserve hashes/versions, provenance, taxonomy, inclusion/exclusion, annotations/reference protocol, hierarchy, missingness, split/randomization.
## 33. Evidence bundle
Bind plan, manifests, artifacts, results, deviations, limitations, software/configuration, and provenance without auto-verdict.
## 34. Scientific review record
Record reviewer/decision/rationale/scope/limitations/replication status; only external review can support a claim transition.
## 35. Claim restrictions
No statistical threshold, agreement, correlation, SI, judge output, or synthetic test alone validates a claim.
## 36. Data blockers
Independent DQI targets; Layer2 reference annotation; BSDA perturbation data; RC calibrated trajectories; SAEA controlled sequences are absent.
## 37. Implementation blockers
Advanced inference depends on approved B2–C methods, data protocols, and explicit design choices.
## 38. Implementation-ready infrastructure
Metadata-only validation-plan/manifests/evidence/review schemas and deterministic serialization are safe before real studies.
## 39. Experimental work still required
Collect independent appropriately designed data, preregister, execute, analyze, replicate, then obtain scientific review.
## 40. Exact Codex scope
Implement only validation artifact schemas/guards next; do not implement component runners, labels, thresholds, or claim promotion.

## Direct answers

B2: paired and Welch statistics are ready; p-values remain null; Hedges g is deferred; raw mean/paired differences are safe. B3: U, Wilcoxon, and Cliff delta are ready; discard Wilcoxon zeros; rank p-values deferred. B4: explicit IID/paired percentile bootstrap is ready; BCa and defaults for B/confidence are deferred. C: grouped bootstrap precedes mixed models; SciPy first serves CDF/reference work and statsmodels first serves regression/mixed adapters; never hand-write LMM/GLMM; multiplicity/permutation remain future with explicit plans; advanced hierarchy work is blocked pending contracts. D: DQI can begin synthetic sanity first; BSDA may begin pilot empirical validation once matched data exist; Layer 2 needs independent annotation, BSDA needs perturbation/reference data, RC needs calibrated trajectories, SAEA needs isolated controlled sequences. DRAA risk, scalar PRI, and ML predictive validity cannot be claimed now. Safest D work is metadata artifacts. Recommended order: B2, B3, B4, C grouped bootstrap, then D artifacts/pilots/confirmatory work.
