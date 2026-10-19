# SecureLLMBench

SecureLLMBench is a modular Python 3.11+ framework for traceable LLM security and safety benchmarking research. The current repository includes real engineering implementations for dataset ingestion, local inference, benchmark execution, detector evidence, Layer 2 judging infrastructure, BSDA, Recovery Capability, SAEA, DRAA/PRI evidence profiles, ML infrastructure, statistics, persistence, API, and dashboard exploration.

The repository is not a source of scientific claims by itself. Passing tests and fixture dry-runs validate software behavior only. Paper results require real datasets, installed target models, real judge/evaluation providers, approved outcome labels where needed, and explicit statistical review.

## Requirements

- Python 3.11 or later
- For this workspace: `.\.venv\Scripts\python.exe`
- Optional local model execution through Ollama with models installed before running experiments
- Optional OpenAI-compatible endpoint execution, enabled only by the server operator
- Optional semantic embeddings through `pip install -e ".[semantic]"`

## Quick Start

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\api_smoke.py
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
.\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --fixture-dry-run
.\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py --input experiments\paper_2026\outputs\fixture_trace.json
```

Local Ollama run, when models are already installed:

```powershell
.\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --target-model qwen3.5:2b --judge-model gemma3:4b --output experiments\paper_2026\outputs\local_trace.json
.\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py --input experiments\paper_2026\outputs\local_trace.json
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

## Local setup (Windows)

Requires Python 3.11+, Node.js/npm, and a running Ollama service with
`gemma3:4b`, `qwen3.5:2b`, and `llama3.2:3b` already installed. Model downloads
are never automatic; `llama3.2:latest` duplicates the 3B model and is not required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd --prefix frontend install
ollama list
powershell -ExecutionPolicy Bypass -File scripts\start_local.ps1
```

Open http://127.0.0.1:5173. The default ten-prompt check uses five benign and
five red-team prompts. Larger pilots require an explicit separate run.
Tests needing original private annotation packages skip only when those
uncommitted packages are missing; independent labels and calibration remain
required for scientific claims.

Based on SecureLLMBench by vignesh26-09 (Apache-2.0)

## Limitations and validity

Raw pilot outputs are not published.

- Only small local models (2B-4B) were tested; the Gemma judge is 4B. No generalization or production-suitability claims.
- Original pilot: 50 prompts/model; LLM-only labels from small annotators include models under test and possible self-preference bias.
- Synthetic canary set: 25 secret-leak tests, 25 instruction-override/injection tests and 10 benign controls; 180 outputs cached.
- Canary labels cover specified leak/injection tokens only, not all harm categories or factual accuracy; unflagged does not mean safe.
- V0 test leak/injection recall was 5.71% despite system context; selected V3 recall 80% with FPR 45.45% (rounded: 45%).
- Dev/test was retrospective, stratified 90/90 with seed42; earlier full-set results were inspected and prompts may overlap across models.
- There is no true fresh holdout. Small samples, synthetic construction and correlated prompts limit interval interpretation.
- Oracle checks normalize case, punctuation, whitespace/zero-width separators; detect base64/hex/reversal and secret fragments >=12 contiguous original characters.
- Markers require full matches. Only one encoding layer is inspected; normalization and partial matching can create false positives.
- Known-value checks cannot detect unknown secrets or prove absence of disclosure; they are not a general safety classifier.
- Cached oracle sanity: 73/180 fired, no model calls; by-construction matching counts, NOT an accuracy result.
- The expanded oracle is broader than the original exact regex; no new accuracy claim follows from matching the same fixture values.
- Human check, n=30, enriched toward non-safe candidates, not a representative sample; labels: safe=30, unsafe=0, borderline=0; non-safe=0.
- Judge vs human check: raw agreement 90.00%, Cohen's kappa 0.0000, Gwet AC1 0.8950; non-safe recall unavailable (Wilson 95% CI unavailable), precision 0.00% (Wilson 95% CI [0.00%, 56.15%]).
- Human vs LLM-reference agreement 76.67%; LLM-annotated results remain LLM-annotated. This small selected check does not establish population accuracy; larger independent human studies are still needed.

### Recommended usage

- Use deterministic oracle checks wherever a secret/marker is known; use the LLM judge for open-ended cases and triage.
- Optional stand-alone config: configs/judge_variants.json; judge_variant=V0 and verdict_mode=llm_only remain defaults.
- Opt in with verdict_mode=hybrid: an oracle hit returns unsafe without a model call; otherwise use the configured LLM judge.
- Run python scripts/judge_devtest.py --case CASE.json --verdict-mode hybrid; case keys: id, system_prompt, user_prompt, output, secrets, markers.
- Retain invalid/abstaining LLM results as unavailable; never substitute a safe result. Match reports contain types only, never secret text.
See the [results summary for the paper and viva](docs/RESULTS_SUMMARY.md) for aggregate evidence and limitations; raw dev/test and oracle reports remain local and are not included in this repository.
Conceptual crosswalk to the pinned OWASP Top 10 for LLM Applications **2025** edition:

| Threat category | OWASP application-risk correspondence |
|---|---|
| Prompt override / jailbreak via instructions | LLM01:2025 Prompt Injection |
| Private-data disclosure | LLM02:2025 Sensitive Information Disclosure |
| System-instruction disclosure | LLM07:2025 System Prompt Leakage |
| Unsupported factual claims | LLM09:2025 Misinformation |
| Violence, hate or fraud content requests | No direct one-to-one application-risk category |
This crosswalk does not establish category coverage or exploits; benign controls are not threats.
Source: [OWASP Gen AI Security Project, 2025 Top 10](https://genai.owasp.org/llm-top-10/).

## Data and raw outputs

Raw pilot/canary outputs and large external datasets are not included in this public snapshot.
Fetch upstream datasets using the acquisition/import helpers in scripts/: scripts/build_10000_corpus.py, scripts/fetch_phase4_jbb_sources.py.
Use the documented script options and source requirements; large source files stay local.
Upstream dataset licences apply and must be checked by the user before fetching or redistribution.

## Security notes

- This app is for local research on localhost only. Do not expose it to a network.
- Sample sign-in is passwordless and accepts loopback requests only.
- Grafana allows anonymous Viewer access on loopback only.
- All accounts share one research workspace. Per-user isolation is not implemented.
- `securellmbench.db` is local and gitignored. Do not share it.
- No demo credentials are included.
