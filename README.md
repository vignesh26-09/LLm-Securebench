# SecureLLMBench

SecureLLMBench is a modular Python 3.11+ framework for traceable LLM security and safety benchmarking research. The current repository includes real engineering implementations for dataset ingestion, local inference, benchmark execution, detector evidence, Layer 2 judging infrastructure, BSDA, Recovery Capability, SAEA, DRAA/PRI evidence profiles, ML infrastructure, statistics, persistence, API, and dashboard exploration.

The repository is not a source of scientific claims by itself. Passing tests and fixture dry-runs validate software behavior only. Paper results require real datasets, installed target models, real judge/evaluation providers, approved outcome labels where needed, and explicit statistical review.

## Requirements

- Python 3.11 or later
- For this workspace: `F:\SecureLLM\.venv\Scripts\python.exe`
- Optional local model execution through Ollama with models installed before running experiments
- Optional OpenAI-compatible endpoint execution, enabled only by the server operator
- Optional semantic embeddings through `pip install -e ".[semantic]"`

## Quick Start

```powershell
$env:TEMP='F:\SecureLLM.tmp'
$env:TMP='F:\SecureLLM.tmp'
F:\SecureLLM\.venv\Scripts\python.exe -m pytest
F:\SecureLLM\.venv\Scripts\python.exe scripts\api_smoke.py
powershell -ExecutionPolicy Bypass -File scripts\start_local.ps1
```

Dashboard:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

## Implemented

- Dataset ingestion and preprocessing for JSON, JSONL, and CSV.
- Optional semantic dataset analysis and exploratory DQI.
- Provider-neutral model registry and inference contracts.
- Deterministic mock inference for tests.
- Local Ollama inference for installed models only; no automatic downloads.
- A dedicated dashboard benchmark workspace with three open-weight Ollama showcase presets (Gemma 3 4B, Qwen 3.5 2B, and Llama 3.2 3B), installed-model discovery, live job state, and links to saved evidence.
- Opt-in OpenAI-compatible inference for user-supplied HTTPS endpoints. Credentials are held only by the active job and are excluded from persisted configurations, responses, logs, and dashboard records.
- Optional local Transformers adapter.
- Benchmark execution and JSON run storage.
- Layer 1 rule, keyword, and pattern detector evidence.
- Layer 2 judge contracts, orchestration, mock provider, and local Ollama judge provider.
- BSDA four-component profile computation plus concrete semantic/safety/instruction adapters.
- Recovery Capability runtime following `docs/RECOVERY_CAPABILITY_IMPLEMENTATION_SPEC.md`.
- SAEA computation over pre-generated matched behavioral states.
- DRAA Modes A/B evidence transport with `risk_score = None`.
- PRI Modes A/B profile records with `scalar_pri = None`.
- ML prediction schemas, leakage checks, grouped splits, train-only preprocessing, and engineering baselines.
- Descriptive, correlation, rank, bootstrap, and parametric statistics utilities with explicit undefined states.
- SQLAlchemy persistence, FastAPI read APIs, local run API, and dashboard.
- Paper 2026 fixture dry-run and analysis scaffold under `experiments/paper_2026/`.

## Not Scientifically Validated

- BSDA, RC, and SAEA empirical novelty or effectiveness claims.
- DRAA scalar risk; it is intentionally not implemented.
- PRI scalar score or model ranking; it is intentionally not implemented.
- ML prediction claims without independent labels and leakage-reviewed task definitions.
- Attack success rate without an explicit versioned outcome-evaluation contract.
- Layer 1 detector evidence as ground truth.
- Layer 2 judge output as ground truth or calibrated probability.

## Running a Dashboard Benchmark

Open **Run benchmark** in the dashboard. A local run can use only a model already installed in the local Ollama service; the dashboard never downloads a model. The three showcase entries are selectable presets, not claims that those models are installed, tested, or validated.

The local startup script enables loopback-only local execution. To allow an OpenAI-compatible endpoint in a controlled deployment, the server operator must explicitly set `SECURELLM_ENABLE_REMOTE_RUNS=1` before starting the API. Remote URLs must use HTTPS unless they target `localhost`, `127.0.0.1`, or `::1`. A submitted key is used for the active request only and is not written to the database or returned by the API.

The dashboard defaults to a fast ten-prompt response check: five benign and five red-team source prompts sampled without replacement within a rotation cycle. It makes one target-model call per prompt, no judge calls, and saves responses, timing, detector-native evidence, source identity, and sample allocation. The controlled 50-prompt pilot and full 10,000-prompt run remain separate choices; they collect the additional observations needed for BSDA, recovery, and SAEA. The fast check does not measure those controlled metrics or establish a validated security ranking. The 50-prompt run can be stopped and resumed with its original allocation.

## Paper Dry-Run

Fixture dry-run:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --fixture-dry-run
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py --input experiments\paper_2026\outputs\fixture_trace.json
```

Local Ollama run, when models are already installed:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --target-model qwen3.5:2b --judge-model gemma3:4b --output experiments\paper_2026\outputs\local_trace.json
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py --input experiments\paper_2026\outputs\local_trace.json
```

See [PAPER_REPRODUCIBILITY.md](docs/PAPER_REPRODUCIBILITY.md) for the full trace and blocker matrix.

## Frontend

```powershell
cd frontend
npm run typecheck
npm run lint
npm test -- --run
npm run build
```

The dashboard displays persisted records and provenance. It separates empty data, missing prerequisites, API failures, and scientific non-validation states.
