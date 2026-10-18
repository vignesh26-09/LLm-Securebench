# SecureLLMBench Paper 2026 Experiment Scaffold

This directory contains the traceable experiment runner and analysis command for paper-readiness work.

The fixture dry-run is engineering-only. It validates trace shape, provenance, metric wiring, null handling, and export behavior. It is not a paper result.

Run the fixture dry-run:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --fixture-dry-run
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py --input experiments\paper_2026\outputs\fixture_trace.json
```

Run against local Ollama models only after the target and judge models are already installed:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --target-model qwen3.5:2b --judge-model gemma3:4b
```

The runner does not download models, invent labels, create BSDA composites, create DRAA risk scores, or create scalar PRI values.
