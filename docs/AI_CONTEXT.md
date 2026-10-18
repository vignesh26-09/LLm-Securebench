# AI agent context for SecureLLMBench

## What this project is

SecureLLMBench is a modular Python 3.11+ framework intended for LLM
security/safety benchmarking research. The current working focus is the dataset
subsystem, not a dashboard, database, model-inference product, or completed
research benchmark.

## Current phase

The repository has completed its current Phase 1–3 engineering scope:

- Phase 1: project skeleton and clean-architecture boundaries.
- Phase 2: validated JSON/JSONL/CSV dataset ingestion and deterministic dataset
  processing.
- Phase 3: optional semantic dataset analysis and exploratory DQI.

These are engineering milestones, not proof of scientific validity.

## Current architecture

- `core/` contains framework-independent schemas and ports.
- `core/dataset/` contains the implemented loading, validation, normalization,
  duplicate, split, statistics, semantic, and DQI modules.
- `apps/api/` contains only a framework-neutral health placeholder.
- `core/models/` and `core/inference/` provide provider-neutral registry and
  inference contracts, an in-memory registry, deterministic mock, and optional
  local Transformers adapter. Other domains remain protocols/placeholders:
  benchmark, detection, judging, research metrics, prediction, and statistics.
- `scripts/process_dataset.py` is the current dependency-free end-to-end dataset
  command. Tests use the standard library's `unittest`.

## What is implemented

Dataset schemas, source loaders, validation, normalization, exact SHA-256
duplicates, deterministic splitting, descriptive statistics, optional embeddings,
cosine similarity, near duplicates, optional clustering adapters, coverage,
difficulty/category analysis, novelty estimation, and an exploratory DQI are
implemented. SentenceTransformers/scikit-learn/HDBSCAN are optional, lazy-loaded
dependencies; the base package remains dependency-free.

Model metadata, an in-memory registry, generation configuration, structured
results, deterministic mock inference, and an optional CPU local-Transformers
provider are implemented. No model is downloaded automatically. Remote/API
providers remain abstractions only.

## Do not change casually

- Do not change `DatasetRecord` validation, normalization, duplicate semantics,
  splitting behavior, or DQI formula without an explicit task and new tests.
- Do not describe DQI as scientifically validated. It is exploratory.
- Do not claim future metrics (including BSDA, SAEA, DRAA, PRI), ML prediction,
  detection/judging implementations, remote/API inference providers, or a
  dashboard are present.
- Preserve the ports-and-adapters dependency direction: infrastructure depends on
  `core`, not the reverse.
- Avoid adding mandatory/GPU-only dependencies for optional semantic capabilities.

## Research status

The code provides diagnostics and a composite research aid, not validated research
findings. Ground truth, annotation policy, datasets in scope, thresholds,
baselines, ablations, and independent validation remain open research work.

## Before making changes

1. Read `README.md`, `docs/architecture.md`, `docs/DATASET_SPEC.md`, and
   `docs/METRICS.md`.
2. Inspect the affected modules and their tests under `tests/`.
3. Keep scope explicit: documentation-only, infrastructure, or research work.
4. Add/update deterministic tests for any behavior change.
5. Run `python -m unittest discover -s tests -p "test_*.py"` and
   `python -m scripts.smoke_check` before reporting completion.
