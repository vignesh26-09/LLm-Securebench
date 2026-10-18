# Paper Claim Risk and Numerical Consistency Audit

## Claim-risk audit

The authoritative paper-evidence bundle does not contain an unqualified claim
that the local pilot is a model comparison or that the Gemma judge replaces
human labels. The following risks remain when drafting the paper:

| Risky shortcut | Why it is unsupported | Required replacement |
|---|---|---|
| “The judge is reliable/validated.” | Kappa is 0.211261 under one fixed mapping. | “The current judge is not sufficiently validated to replace independent human labels.” |
| “53.898% agreement is better than random.” | Raw agreement alone does not establish this. | Report raw agreement and kappa without such interpretation. |
| “Gemma is biased.” | The confusion matrix is asymmetric but does not establish cause. | “The observed disagreement is strongly asymmetric.” |
| “Qwen/Gemma comparison” or “safer model.” | The three-case local pilot is engineering-only. | “Local engineering demonstration.” |
| “ASR” for SAEA CV_obs. | CV_obs is observed cumulative vulnerability. | Use the canonical term and state it is not ASR. |
| “Risk score” or “security grade.” | DRAA and PRI are uncalibrated and have no validated scalar. | Describe diagnostics or profiles with their status. |
| “ML predicts safety.” | No production labels or predictive validation exist. | “ML infrastructure is implemented; predictive performance is not established.” |

Historical documents such as `docs/DASHBOARD_BACKEND_CONTINUATION.md` and
`docs/LOCAL_PIPELINE_AUDIT.md` are implementation/audit context. Their phrases
such as “production build” or “verified result” must not be cited as evidence
of production readiness or scientific validation. Use the paper evidence
manifest and freeze report instead.

## Numerical-consistency audit

**Result: PASS.** The authoritative artifacts agree on the following values:

| Quantity | Exact stored value | Paper display value |
|---|---:|---:|
| Source N | 300 | 300 |
| Usable N | 295 | 295 |
| Coverage | 0.9833333333333333 | 98.333% |
| Raw agreement | 0.5389830508474577 | 53.898% |
| Cohen's kappa | 0.2112609601698581 | 0.211261 |
| Confusion matrix | [[51, 1], [135, 108]] | 51, 1, 135, 108 |

Rounded mentions of 0.539 agreement and 0.211 kappa in methodological or
freeze prose are compatible with the exact stored values. No conflicting
calibration value was found in the authoritative manifest, freeze report,
table artifacts, or calibration-verification artifact.
