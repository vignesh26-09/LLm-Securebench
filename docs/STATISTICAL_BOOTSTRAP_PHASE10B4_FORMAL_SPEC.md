# Phase 10B.4 simple bootstrap uncertainty
## 1. Purpose
Define opt-in IID/paired percentile bootstrap, not universal uncertainty or validation.
## 2. Scope
IID caller-confirmed independent units and complete-pair bootstrap only.
## 3. IID bootstrap
Sample n units with replacement per replicate only after 10B.1 independence acknowledgement.
## 4. Paired bootstrap
Sample complete pairs as indivisible units; never independently resample sides.
## 5. Bootstrap plan
Require callback/identifier, unit, B, confidence, interval method, pairing status; seed optional and recorded. No defaults.
## 6. Callback/statistic interface
Each replicate callback returns one finite scalar of a stable declared type.
## 7. Random sampling
Use a local seeded RNG when seed supplied; record nondeterministic seed absence.
## 8. Paired preservation
Pair IDs and orientation travel together in each sampled pair.
## 9. Percentile interval
Only percentile method: quantiles `(1-c)/2` and `1-(1-c)/2` over sorted valid replicates.
## 10. Quantile convention
Use 10B.1 inclusive linear interpolation at position `(n-1)q`.
## 11. Invalid configuration
Empty input, invalid B/confidence/method, or incompatible pairing is invalid/not applicable.
## 12. Replicate failures
Count undefined/exception/nonfinite failures. Without explicit caller failure policy, any failed replicate yields not-computed; no acceptable failure proportion exists.
## 13. Deterministic seeds
Seed is optional; supplied seed must reproduce draws under same implementation.
## 14. Numerical behavior
Constant valid statistic gives equal endpoints; all failed is undefined; vector/callback type changes are invalid.
## 15. Result schema
Store requested/valid/failed count, confidence, B, seed, method, callback identity, interval nullable, warnings/status/provenance.
## 16. Clustering block
Grouped/nested/repeated input is not applicable without prior independent reduction.
## 17. Scientific limitations
Interval validity depends on resampling unit/design; it never validates a claim.
## 18. Edge tests
Seed/no seed, invalid configuration, n=0/1, constant, partial/all failure, nonfinite/vector callback, paired preservation.
## 19. Implementation scope
Only explicit IID/paired percentile bootstrap after B.1–B.3 contracts.
## 20. Deferred hierarchical bootstrap
BCa, grouped, nested, and attack/session hierarchy bootstrap are Phase 10C.
