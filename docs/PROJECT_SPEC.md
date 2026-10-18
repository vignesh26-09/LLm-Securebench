# SecureLLMBench project specification

## Purpose

SecureLLMBench is a modular Python framework intended to support research and
benchmarking of large-language-model security and safety. The repository is
designed so dataset work, model integrations, benchmark execution, detection,
semantic judging, metrics, prediction, statistics, and delivery mechanisms can
evolve independently.

## Current architecture

The project follows ports-and-adapters (clean architecture) principles.

- `core/` owns framework-independent schemas, protocols, and use-case boundaries.
- `apps/` is the delivery boundary. The current API is a framework-neutral health
  placeholder, not a running web service.
- Concrete adapters may depend on `core`; `core` must not depend on an LLM SDK,
  database, web framework, or a particular dataset source.
- The dataset subsystem is the current substantive implementation. Optional
  semantic adapters are lazy-loaded so base usage stays dependency-free.

## Directory structure

| Directory | Current role |
| --- | --- |
| `apps/api/` | Framework-neutral API health placeholder. |
| `configs/` | Configuration shape placeholder. |
| `core/dataset/` | Dataset schemas, loading, processing, semantic analysis, and exploratory DQI. |
| `core/models/`, `core/inference/` | Provider-neutral registry and inference contracts, mock provider, and optional local Transformers adapter. |
| `core/benchmark/`, `detection/`, `judging/`, `metrics/`, `prediction/`, `statistics/` | Protocols and minimal domain types only. |
| `data/` | Raw, external, interim, and processed-data layout; includes a small example input. |
| `docs/` | Architecture, development, dataset, metrics, and research documentation. |
| `experiments/` | Reserved for reproducible experiment definitions and results. |
| `scripts/` | Dependency-free smoke check and dataset-processing CLI. |
| `tests/` | Standard-library unit tests. |

## Implemented functionality

The current implementation provides:

- Python 3.11+ package metadata and standard-library test execution.
- Dataset schemas: `DatasetRecord`, `DatasetMetadata`, `DatasetVersion`, and
  immutable `Dataset` collections.
- JSON, JSONL, and CSV dataset loaders behind the `DatasetLoader` protocol.
- Explicit record validation, text normalization, SHA-256 exact-duplicate
  grouping, deterministic train/evaluation splitting, and descriptive statistics.
- Optional CPU-oriented semantic analysis interfaces: embeddings, cosine
  similarity, near-duplicate pairs, and optional DBSCAN/HDBSCAN adapters.
- Dataset coverage, difficulty distribution, category balance, novelty estimate,
  and a configurable exploratory DQI.
- A CLI that loads, normalizes, and summarizes a supported small dataset.
- A framework-neutral API health object and health smoke check.
- Model metadata and an in-memory registry, structured inference contracts,
  deterministic mock inference, and a lazy optional CPU local-Transformers
  provider that does not download models automatically.

## Planned functionality

The following areas have package boundaries but no production implementation:

- benchmark execution and model-provider integrations beyond the mock and local
  Transformers adapter;
- Layer 1 detection and Layer 2 semantic judging implementations;
- research metrics beyond the present exploratory dataset metrics;
- ML prediction, statistical-analysis implementations, persistence, database,
  dashboard, and production HTTP API;
- scientific validation of DQI and any future research metric.

## Development principles

- Keep domain contracts independent from infrastructure adapters.
- Add only dependencies required by a concrete supported capability.
- Keep optional integrations lazy-loaded and CPU-compatible by default.
- Validate external data at the system boundary and preserve source-specific
  fields in `metadata` rather than expanding the core schema casually.
- Cover deterministic behavior with unit tests before extending the pipeline.
- Treat exploratory metrics as research instruments, not validated claims.
