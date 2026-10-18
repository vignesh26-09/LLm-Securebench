# SAEA implementation

`core.saea` implements the reconciled SAEA contract over **pre-generated**
behavioral states. It does not invoke a model, a judge, an embedding provider,
BSDA, or RC.

## Architecture

`SAEAInput -> SAEAEngine -> SAEAResult`

The input contains an ordered sequence of `AttackInstance` objects, session
baseline states, isolated `Delta`-scale controls, optional existing RC recovery
windows, coalition evaluations, and reproducibility/calibration metadata.
`BehavioralState` uses named `[0,1]` scores; `safety` and `helpfulness` are
required. Provider/version and judge uncertainty belong in state provenance.

BSDA is retained only as a separate reference on an attack instance. SAEA never
uses BSDA's own scale in its arithmetic. RC is linked through `RecoveryWindow`;
SAEA does not calculate or reinterpret RC.

## Implemented definitions

- `Delta_i = normalized_euclidean(state_i, baseline)`
- `V_iso^Delta(A_i) = normalized_euclidean(isolated_state_i, isolated_baseline_i)`
- `DeltaV_i = Delta_i - V_iso^Delta(A_i)`
- `CV_obs = mean(Delta_i)`
- `E_Bliss = 1 - product(1 - V_iso^Delta(A_i))`
- `SI = CV_obs / E_Bliss`

`SI` is not applicable when `E_Bliss` is exactly zero, or when an explicit
calibration artifact supplies a near-zero gate it meets. No epsilon is added.
Bliss independence remains a candidate null model, not a validated assumption.
No bounded SI and no composite security score are produced.

Exact Shapley attribution accepts pre-generated coalition `CV_obs` values for
all subsets up to 10 attack instances. Coalition order is original sequence
position. Larger sampled attribution requires a calibration-configured target
standard error and pre-generated permutation evaluations; otherwise it returns
an explicit unavailable status.

Recovery trend uses raw, RC-applicable gaps only. Stacked sequences are not
applicable; fewer than three eligible gaps are insufficient data. Gap positions
are retained even when other gaps are excluded.

## Statistics and limitations

`bootstrap_synergy` resamples defined independent session SI values only. Its
defaults (`1000`, `0.95`, seed `0`) are reproducibility conventions inherited
from RC, not scientifically validated thresholds. Friedman/mixed-effects order
testing and growth-curve selection are dependency-inverted ports: the approved
methodology leaves their fitting/configuration choices to a pre-registered
statistics adapter.

Results preserve run, sequence, model, dataset, methodology, calibration, and
seed provenance. Missing baselines, controls, context validity, failed
evaluations, incompatible dimensions, and insufficient data remain explicit
statuses rather than zero values.

SAEA is exploratory. It does not prove attack success, judge-ground truth,
robustness, causal independence, or scientific validity.
