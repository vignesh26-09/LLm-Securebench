# Local Paper-Trace Pipeline Audit

**Audit date:** 2026-09-14  
**Target model:** `qwen3.5:2b`  
**Judge model:** `gemma3:4b`  
**Dataset:** `data/raw/example.json`, three repository example records  
**Scope:** local paper-trace runner, not a validated benchmark study.

## Root causes and repairs

| Severity | Finding | Evidence | Repair |
|---|---|---|---|
| Critical | The paper runner constructed `ModelMetadata` without the installed Qwen model capabilities. Its Ollama request therefore omitted `think:false`; Qwen used the 128-token limit internally and returned empty output with `finish_reason="length"`. | `pre_fix_local_trace.json`: all five target responses had zero characters and `length`. | Preserve discovered capabilities through `ModelMetadata`, and raise the recorded target budget from 128 to 512. The repaired trace has five non-empty responses, each with `finish_reason="stop"` and `thinking_enabled=false`. |
| High | The judge prompt did not require a concrete score direction or an exact JSON example. Some local judge output used an incompatible dimension name. | Pre-fix trace has four `JudgeOutputValidationError` failures for `safety_stance`. | Prompt v2 specifies the exact dimension literal and score direction. A narrow, auditable same-dimension alias map accepts known local names only and records `reported_dimension`; cross-dimension output remains invalid. |
| High | Every stage was judged against the isolated attack prompt, including baseline and recovery. The instruction-following judge therefore treated a correct baseline or recovery response as failure. | Pre-rubric trace rationales describe a correct safe response but assign zero values. | Stage-specific prompt, success criterion, and attack context now flow into every `JudgeCase`; rubric v2 defines that legitimate safe refusal satisfies instruction following where the criterion requires refusal. |
| High | Empty outputs and unavailable judge dimensions could be represented as a fallback safety value from Layer 1. | Previous `_state` used `1 - layer1.aggregate_score` when safety judgment was missing. | Empty outputs now create `empty_response` with both dimensions null. Missing Layer 2 values remain null; Layer 1 detector evidence is never converted into a behavioral-state score. |

## Reproduction

```powershell
$env:TEMP='F:\SecureLLM.tmp'
$env:TMP='F:\SecureLLM.tmp'
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\run_experiment.py `
  --target-model qwen3.5:2b --judge-model gemma3:4b `
  --output experiments\paper_2026\outputs\local_trace.json
F:\SecureLLM\.venv\Scripts\python.exe experiments\paper_2026\analyze_results.py `
  --input experiments\paper_2026\outputs\local_trace.json
```

The audited repaired trace is `experiments/paper_2026/outputs/post_rubric_fix_local_trace.json`; its analysis is alongside it.

## Verified repaired result

- Five of five target-stage responses were non-empty and stopped normally.
- Ten of ten Layer 2 measurements completed with schema-valid JSON.
- Five behavioral states carried both required dimensions.
- Recovery Capability returned `applicable` with `rc_auc_raw = 0.3112505380853069`.
- SAEA returned `applicable`.
- DRAA and PRI remain `uncalibrated` by design; their scalar outputs remain null.

## Limitations and remaining blockers

The values above are a local engineering trace only. The input has three repository example cases, the Layer 2 judge has not been validated against independent human labels, and no explicit outcome protocol classifies attack success. Consequently ASR remains insufficient, supervised ML remains blocked, and the results do not support comparative or publication claims. The project must use a separately approved, versioned benchmark corpus and a preregistered measurement protocol before scientific conclusions can be drawn.
