# Phase 10C hierarchy-aware inference
## 1. Purpose
Provide staged dependence-aware infrastructure, not one automatic statistics package.
## 2. Scope
Future grouped/nested resampling, permutation, multiplicity, and model adapters.
## 3. Hierarchy representation
Use optional declared model/dataset/category/family/base-case/variant/run/session/turn IDs; never fabricate IDs.
## 4. Grouped bootstrap
Resample declared parent clusters, retaining children, pairing, duplicate cluster draws, and cluster/observation statistic semantics.
## 5. Hierarchical bootstrap
Only explicit plan levels are resampled; top-level-only bootstrap may be preferable depending on estimand.
## 6. Exchangeability
Require a declared design argument; no generic row shuffle.
## 7. Permutation/randomization
Require unit, block, transformation, statistic, randomization/exchangeability provenance.
## 8. Monte Carlo permutation
Future plan records count/seed; finite-sample formula is configuration/documented methodology, not an alpha rule.
## 9. Exact permutation
Only when explicitly feasible under declared design; no automatic enumeration.
## 10. Multiplicity
Require family, raw p-values, method, and supplied error-rate target.
## 11. Bonferroni
Future FWER adapter only; no default family mapping.
## 12. Holm
Future step-down FWER adapter only.
## 13. BH
Future FDR adapter only.
## 14. Regression architecture
Future adapter preserves formula, effects, family/link, optimizer, backend, mappings, warnings, assumptions, provenance.
## 15. Mixed-model architecture
Random effects follow declared sampling design, never merely available IDs.
## 16. Dependency assessment
SciPy supports CDF/reference needs; statsmodels is future regression/mixed-model dependency.
## 17. Convergence
Nonconvergence is a status/warning, never zero effect.
## 18. Covariance/inference strategy
Record model-based, robust, GEE, or resampling strategy explicitly; none is universal.
## 19. Missingness
Reuse explicit 10A plans; never zero-fill.
## 20. Grouping validation
Require actual group identities, parent structure, and dependence role.
## 21. Result schemas
Record coefficients/statistics/interval/p-values only when computed, plus backend/convergence/provenance.
## 22. Reproducibility
Persist plan, hashes, hierarchy, seed, code/dependency versions.
## 23. Edge tests
Missing groups, crossing pairing, duplicate sampled clusters, invalid levels, exchangeability absence, convergence failures.
## 24. Staged implementation
10C.1 grouped bootstrap; 10C.2 hierarchical bootstrap; 10C.3 permutation; 10C.4 multiplicity; 10C.5 adapters.
## 25. Methods safe now
No hierarchy-aware inference code is authorized before an approved implementation task; metadata already exists.
## 26. Dependency-gated methods
SciPy CDF/testing; statsmodels regression/mixed models.
## 27. Blocked methods
Hand-written LMM/GLMM, automatic random effects, generic shuffling.
## 28. Exact Codex scope
Implement grouped bootstrap first only after B4 and explicit resampling-plan/cluster tests.
