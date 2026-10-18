# Paper Evidence Manifest

| Claim/result | Exact value | Source artifact | Producing script | Dataset/configuration | N | Status |
|---|---:|---|---|---|---:|---|
| JailbreakBench source records | 300 | `results.json`; source manifest | `validate_jailbreakbench_judge.py` | revision `b2b462fd32ca655e0bdfc70b68155720977f4d69`, SHA-256 `dacaf76a1057785f11b0fc6aa07b9a73cdab588319ddfc5e8cef2909e5b112a5` | 300 | empirical, exploratory calibration |
| Usable judge records | 295 | `results.json` | `build_paper_evidence.py` recomputation | local `safety_stance` judge, threshold `0.5` | 300 | empirical, exploratory calibration |
| Coverage | 98.333% | `calibration_verification.json` | `build_paper_evidence.py` | same as above | 300 | empirical, exploratory calibration |
| Raw agreement | 53.898% | `calibration_verification.json` | `build_paper_evidence.py` | source `human_majority`; fixed predeclared rule | 295 | empirical, exploratory calibration |
| Cohen’s kappa | 0.211 | `calibration_verification.json` | `build_paper_evidence.py` | same as above | 295 | empirical, exploratory calibration; insufficient to replace labels |
| Local engineering demonstration | 4 runs; 12 evaluations; 36 Layer 1 records | SQLite `securellmbench.db` | `run_local_benchmark.py` | repository 3-case example; Qwen/Gemma configurations | 12 | engineering-only; not comparison |
| Layer 2 dashboard availability | 0 persisted records | SQLite `securellmbench.db` | n/a | dashboard database | 0 | absent |

Confusion matrix: `pred_0_label_0=51`, `pred_0_label_1=1`, `pred_1_label_0=135`, `pred_1_label_1=108`.

Claims not supported: calibrated human-equivalent judge, ASR, statistical significance, model ranking, novelty, general safety claims, ML prediction utility, DRAA scalar risk, or PRI scalar score.
