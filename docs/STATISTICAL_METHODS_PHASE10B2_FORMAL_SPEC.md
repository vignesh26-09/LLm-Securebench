# Phase 10B.2 parametric statistics and safe effects
## 1. Purpose
Define dependency-free paired and Welch statistic contracts, not scientific decisions.
## 2. Relationship to 10A/10B.1
Use 10A readiness/grouping/pairing/missingness metadata and 10B.1 finite inputs/guards.
## 3. Scope
Paired t statistic, Welch statistic, raw contrasts, and nullable result metadata only.
## 4. Paired t contract
For complete declared pairs `d=x-y`, compute dbar, sample sd, `SE=sd/sqrt(n)`, `t=dbar/SE`, `df=n-1`; require n>=2.
## 5. Welch contract
For declared independent groups n1,n2>=2, compute `t=(mean_x-mean_y)/sqrt(sx²/nx+sy²/ny)` and Welch-Satterthwaite df. Student pooled t is excluded.
## 6. Alternatives
Preserve `two_sided`, `greater`, or `less` as metadata only; no p-value is calculated.
## 7. Zero variance behavior
All-zero paired differences and constant nonzero paired differences are undefined (no fabricated infinity). One zero-variance Welch group is computable if SE>0; both constant groups are undefined whether equal or different.
## 8. Clustering/pairing guards
Apply 10B.1 structured-reduction guard and explicit pairing rules; contradictory design is not applicable.
## 9. P-value boundary
Return statistic/df/alternative and `p_value=None`. Student-t CDF is deferred pending approved SciPy capability.
## 10. Raw effects
Return oriented raw mean difference and paired mean difference, never magnitude labels.
## 11. Standardized effect decision
Defer standardized paired and Hedges g: denominator conventions remain unresolved. Independent standardized effects are also deferred until separately approved.
## 12. Numerical stability
Use finite checks, two-pass sample variance, and explicit numerical failure on overflow/invalid denominator.
## 13. Result schema
Use computation status, n total/valid, estimate, statistic, df, alternative, omitted counts, notes, guards/provenance; interval/p-values remain null.
## 14. Assumptions
Record, never auto-test: declared pairing/independent units, sampling structure, mean-difference estimand, and suitable difference/group behavior.
## 15. Edge tests
Hand-computed/positive/negative/zero/constant/one-pair/missing/mismatch/cluster paired cases; equal/unequal mean/variance/n, constants, n=1, and clustering Welch cases.
## 16. Dependency policy
Standard library is sufficient for statistic/df; SciPy is future optional CDF/reference support.
## 17. Implementation-ready scope
Statistic/df/raw contrasts/status handling are engineering-ready.
## 18. Deferred scope
p-values, CIs, standardized effects, bootstrap, power, and validation runners.
## 19. Blockers
No declared independent unit, unresolved pairing, or non-finite values block computation.
## 20. Exact Codex scope
Implement only paired/Welch statistic+df with existing guards and nullable p-values.
