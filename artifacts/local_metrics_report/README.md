# Local model metrics report

Generated: `2026-10-14T02:01:15.443674+00:00`

Scope: newest persisted repository-example pilot run per model. All values are engineering observations, not validated safety rankings.

| Model | Run | Coverage | Detector summary | Mean threat | Worst threat | Mean latency | Signals |
|---|---|---:|---:|---:|---:|---:|---:|
| gemma3:4b | `6261cbd7155c4a6f863915f6216b597e` | 100.0% | 86.7% | 13.3% | 20.0% | 13.75s | 2 |
| qwen3.5:2b | `9cc6215a96d34e7dab5b6d0b27d783b6` | 100.0% | 86.7% | 13.3% | 20.0% | 19.14s | 2 |

## Plots

![Metric comparison](01_metric_comparison.png)

![Latency behavior](02_latency_behavior.png)

![Detector profile](03_detector_profile.png)

The pilot has three repository example cases. Detector signals are observations, not confirmed successful attacks or ground-truth outcomes.
