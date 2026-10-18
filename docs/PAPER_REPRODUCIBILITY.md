# Paper Reproducibility

This document records how to reproduce the current SecureLLMBench paper-readiness scaffold. It does not claim that the included fixture trace is a scientific result.

## Environment

Use the project workspace and interpreter:

```powershell
cd F:\SecureLLM
$env:TEMP='F:\SecureLLM.tmp'
$env:TMP='F:\SecureLLM.tmp'
F:\SecureLLM\.venv\Scripts\python.exe -m pytest
```

No default test requires internet access, live Ollama, or PostgreSQL.

## Dataset Provenance

The current runnable fixture uses `data/raw/example.json`.

The dataset is a repository engineering example. It is not a validated research corpus. Its records are preserved by hash and provenance before any analysis output is created.

## Model Identities

Fixture dry-run uses deterministic mock inference and mock judging. That validates trace shape only.

Local experimental mode uses installed Ollama target and judge models. The runner does not pull or download models.

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --target-model qwen3.5:2b --judge-model gemma3:4b --output experiments\paper_2026\outputs\local_trace.json
```

## Experiment Command

Fixture:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --fixture-dry-run --output experiments\paper_2026\outputs\fixture_trace.json
```

Local Ollama:

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py --target-model <installed-target-model> --judge-model <installed-judge-model> --output experiments\paper_2026\outputs\local_trace.json
```

## Analysis Command

```powershell
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py --input experiments\paper_2026\outputs\fixture_trace.json --output experiments\paper_2026\outputs\fixture_analysis.json
```

The analysis currently exports descriptive summaries and a Spearman correlation where explicit pairing exists. ASR, supervised ML, and confirmatory claims remain blocked without their prerequisites.

## Output Locations

- Trace JSON: `experiments/paper_2026/outputs/*.json`
- Local benchmark JSON artifacts: `experiments/local-runs/*.json`
- Local SQLite dashboard database: `securellmbench.db` when using local commands

Generated local databases, logs, build outputs, and temp files are ignored by Git.

## Trace Coverage

The paper runner exports:

- dataset identity and hash;
- target model identity;
- generation configuration;
- baseline prompt and response;
- isolated attack prompt and response;
- sequential attack prompts and responses;
- recovery probe and response;
- Layer 1 detector evidence;
- Layer 2 judge measurements;
- behavioral states;
- BSDA four-component result;
- Recovery Capability result;
- SAEA result with matched controls;
- DRAA evidence record with `risk_score = null`;
- PRI profile record with `scalar_pri = null`;
- descriptive statistics;
- ASR status from explicit classified outcome labels only;
- blinded human-validation export and agreement utilities;
- explicit paper blockers.

## Real vs Mock Matrix

| Component | Mock test implementation | Real implementation | Real external dependency | Synthetic fixture only? | Paper-usable today? | Remaining blocker |
| --- | --- | --- | --- | --- | --- | --- |
| Inference | `MockInferenceProvider` | Ollama and optional Transformers adapters | Installed local model | No | Partly | Paper model set and locked versions |
| Layer 1 | Deterministic detector tests | Regex, keyword, pattern detectors | None | No | As evidence only | Not ground truth or universal ASR |
| Layer 2 | `MockJudgeProvider` | Ollama local judge provider | Installed judge model | No | Measurement only | Judge validation against independent labels |
| BSDA | Fake embedding tests | Four-component computation and adapters | Optional local embedding model | No | Exploratory | Calibration and empirical validation |
| Recovery Capability | Unit states | Typed RC runtime | External calibration artifact | No | Formula-ready | Real compatible calibration artifact |
| SAEA | Synthetic behavioral states | Deterministic SAEA engine | Pre-generated matched states | No | Formula-ready | Real matched sequential trajectories |
| DRAA | Evidence fixtures | Mode A/B evidence transport | Upstream evidence | No | Diagnostic only | Mode C/risk intentionally absent |
| PRI | Profile fixtures | Mode A/B profile records | Upstream evidence | No | Diagnostic only | Scalar/ranking intentionally absent |
| ML | Fixture baselines | Leakage-safe baseline infrastructure | Real independent labels | Yes for current tests | No | Independent labels and target contract |
| ASR | Empty-label blocked output | Versioned classified outcome records and denominator policy | Approved evaluator labels | No | No | Outcome protocol and labels |
| Human validation | Unit-test label fixtures | Blinded sample export, agreement, kappa, confusion matrix | Independent raters | No | Workflow-ready | Real rater protocol and adjudication |
| Statistics | Unit vectors | Descriptive/correlation/rank/bootstrap/t-tests | None | No | Descriptive/exploratory | Preregistered plan and assumptions |
| Persistence | SQLite tests | SQLAlchemy/FastAPI APIs | SQLite/PostgreSQL-compatible URL | No | Engineering-ready | Production auth/lifecycle policy |

## Scientific Boundaries

The implementation preserves these safeguards:

- BSDA has no scalar composite.
- DRAA `risk_score` remains null.
- PRI `scalar_pri` remains null.
- RC scores remain null when uncalibrated, incompatible, undefined, or not applicable.
- Missing, failed, not-applicable, unavailable, uncalibrated, and not-computed values are not replaced with zero.
- Layer 1 detector output is not attack success.
- Layer 2 judge output is not ground truth.
- ML experiments are blocked for real scientific claims unless independent labels exist.
- Statistical outputs do not automatically validate claims.

## Remaining Scientific Blockers

- Approved attack-success outcome contract and ASR denominator policy.
- Real independently labeled or adjudicated outcomes.
- Compatible external RC calibration artifact with positive finite `delta_a_min`.
- Real matched baseline, isolated attack, sequential attack, and recovery trajectories across the selected model/dataset population.
- Layer 2 judge validation against independent human or reference labels.
- Preregistered statistical analysis plan for paper claims.
- Explicit human-validation workflow with blinded exports and rater agreement analysis.
