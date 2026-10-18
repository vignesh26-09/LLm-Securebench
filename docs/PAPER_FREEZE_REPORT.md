# Paper Freeze Report

- Freeze commit: `dcaecd39cbd392df1b2d05bc90a1b876d527e8c1`
- Working-tree status at freeze:
```text
?? SecureLLM.zip
?? artifacts/
?? docs/PAPER_EVIDENCE_MANIFEST.md
?? docs/PAPER_FREEZE_REPORT.md
?? experiments/jailbreakbench-validation/
?? experiments/paper_2026/outputs/
?? scripts/build_paper_evidence.py
```
- Calibration verification: source N=300, usable N=295, coverage=98.333%, raw agreement=53.898%, Cohen’s κ=0.211.
- Confusion matrix: {'pred_0_label_0': 51, 'pred_0_label_1': 1, 'pred_1_label_0': 135, 'pred_1_label_1': 108}.
- Reproduce evidence bundle: `F:\SecureLLM\.venv\Scripts\python.exe scripts\build_paper_evidence.py`
- Verify stored calibration without calling the judge: `F:\SecureLLM\.venv\Scripts\python.exe scripts\verify_persisted_judge_calibration.py`
- Reproduce paper trace: `F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --target-model qwen3.5:2b --judge-model gemma3:4b --output experiments\paper_2026\outputs\local_trace.json`
- Regression: `F:\SecureLLM\.venv\Scripts\python.exe -m pytest -q`; `F:\SecureLLM\.venv\Scripts\python.exe scripts\api_smoke.py`; frontend `npm test`, `npm run typecheck`, `npm run build`.

## Limitations and unsupported claims

The Gemma judge under this fixed rule is not sufficiently validated to replace independent human labels. The three-case local pilot is engineering-only. No ASR, significance, novelty, model ranking, calibrated risk, calibrated recovery probability, or ML predictive claim is supported.
