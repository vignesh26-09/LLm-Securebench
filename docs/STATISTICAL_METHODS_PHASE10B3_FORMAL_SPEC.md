# Phase 10B.3 rank/non-parametric statistics
## 1. Purpose
Define rank statistics without inferential p-values or scientific conclusions.
## 2. Scope
Mann-Whitney U, Wilcoxon signed-rank, rank-biserial effects, Cliff delta, average ranks.
## 3. Ranking
Use deterministic 1-based occupied ranks; equal values receive their average rank.
## 4. Ties
Ties are retained and average-ranked; no no-ties shortcut is used.
## 5. Mann-Whitney
Independent declared groups only: `U1=R1-n1(n1+1)/2`, `U2=n1*n2-U1`; report U1 and U2 with first-group orientation. Require n1,n2>=1.
## 6. Wilcoxon
Paired declared complete pairs only: rank absolute nonzero differences, calculate W+ and W-, report min(W+,W-).
## 7. Zero policy
Discard zero differences and preserve discarded count; all-zero input is undefined.
## 8. Rank-biserial independent
`(U1-U2)/(n1*n2)`, oriented to first group; undefined if denominator zero.
## 9. Rank-biserial paired
`(W+-W-)/(W++W-)` under the stated zero policy; undefined with no nonzero ranks.
## 10. Cliff delta
Independent first-group orientation: `(count(x>y)-count(x<y))/(nx*ny)`; ties contribute zero. O(n*m) is acceptable initially.
## 11. Alternatives
Retain alternative metadata only; no p-values.
## 12. Clustering/pairing
Use 10B.1 guards. Paired data reject U; independent/unknown data reject Wilcoxon.
## 13. P-value boundary
Exact/asymptotic p-values, continuity and tie corrections are deferred.
## 14. Numerical stability
Finite checks and average ranks; non-finite input invalid, no silent omission.
## 15. Result schema
Preserve U/W variants, ranks, zero/tie/omission counts, orientation, status, and p-value null.
## 16. Assumptions
Record independence or pairing, rank/stochastic-order interpretation, and symmetric differences for location interpretation; do not auto-test.
## 17. Edge tests
Disjoint/equal/tied/tiny/reversed/clustered U; zero/one nonzero/tied/positive/negative/mismatch Wilcoxon; dominance/ties Cliff.
## 18. Implementation-ready scope
Rank mechanics, statistics, rank-biserial, and Cliff delta are ready without dependencies.
## 19. Deferred scope
Rank-test p-values, exact enumeration, bootstrap, clustering methods.
## 20. Exact Codex scope
Implement only described statistics with explicit pairing/grouping guards.
