# Production-Scale Experiment Preflight

The supplied scale-up request cannot be executed as a scientific experiment from the current workspace. It has two installed local models (`qwen3.5:2b`, `gemma3:4b`) and one three-record engineering input (`data/raw/example.json`). It has no approved outcome protocol, independently labelled outcomes, rater protocol, or approved 100-case corpus.

Run the preflight before any production execution:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe scripts\production_preflight.py `
  --dataset path\to\approved_corpus.json `
  --model qwen3.5:2b --model gemma3:4b --minimum-cases 100
```

The dataset metadata must identify its source and version. Its `metadata.provenance` must identify an approval, an outcome protocol, an independent label schema, and a rater protocol. The script reports a SHA-256 hash, available and missing local models, and explicit blockers. Passing this operational preflight does not validate the study, its measurements, or its claims.

The existing three-case data may remain useful for engineering smoke tests. It must not be expanded by generated prompts and relabelled as a production corpus, and it must not be used to derive attack-success rates, confidence intervals, novelty claims, or model rankings.
