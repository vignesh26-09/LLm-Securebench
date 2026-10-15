# Evidence gaps and submission gate

This is a **pre-results research draft**. It documents existing backend engineering and a proposed feasibility pilot; it is not a completed empirical study or a model-safety comparison.

## Established now

- The repository has a local benchmark path, Ollama inference adapter, controlled experiment runner, source/protocol checks, immutable observations, human-label workflow, metric applicability rules and provenance-gated reporting. Existing local benchmark and exploratory model calls establish operational evidence only.
- A separate persisted JailbreakBench judge comparison verifies 300 source records, 295 usable pairs, 98.33% coverage, 53.90% raw agreement, Cohen's κ = 0.21126 and TN/FP/FN/TP = 51/135/1/108 under its historical mapping. This does **not** validate a success judge for the proposed exact-secret task.
- The current Phase 6 reviewer state has no authentic independent human labels for the 36 prepared exploratory responses. No semantic ASR or scientific model ranking follows.

## Missing before pilot execution

1. Approve/freeze the feasibility design, exact scripts, legitimate final probes, secret generator and trial assignment. The requirements and novelty ledger are drafted; a completed approved design/tasks lock and completed study are not evidenced.
2. Implement and version the exact-contiguous secret checker and restricted source linkage. Test held-out critical positive/negative, near-miss, wrong-trial, malformed and earlier/final fixtures. Table II is blank because neither implementation nor validation scores exist.
3. Audit the Qwen/Gemma prompt templates and whether the chosen Ollama/runtime exposes a fully rendered prompt. Verify current model digests, `top_p`, `num_ctx`, effective seeds and context-retention evidence; do not infer effective context from request roles alone.
4. Fix the call budget and trial schedule for seven arms, three distances, two models, 20 goals and three repetitions, including any arm-specific non-applicable cells and all filler calls. The present paper does not assert a total budget that has not been derived and approved.
5. Establish restricted secret handling, redacted public exports, source hashes and audit access. Do not release raw trial secrets.

## Missing before empirical claims

- Execute the actual assigned pilot with live defender replies; keep the scripted-history arm separate. Populate execution, failure, truncation, retention and exclusion denominators. Tables V–VIII and Figures 4–6 remain deliberately unfilled.
- Recompute final, earlier and ever exact-disclosure outcomes from eligible persisted responses and the versioned checker. Keep invalid/missing states distinct from negative outcomes.
- Analyze model-specific A–T risk differences at d=2, secondary distances, goal-cluster uncertainty, attrition sensitivity and context-position effects. Prejustify any equivalence margin; pilot sample size cannot support broad rankings by formatting alone.
- Independently validate semantic disclosure or immediate ASR if comparing those constructs with exact risk. Existing BSDA components require calibrated behavioral representations; RC requires eligible calibrated trajectories and a positive initial degradation; SAEA requires matched isolated controls and contamination/context checks. Their formulas were audited in code for this paper, but no validated same-observation scientific values are available for the proposed study.
- Complete human annotation with genuine independent reviewers if broader semantic labels are claimed. The historical safety-stance judge is ineligible as sole truth.
- Extend literature review for unresolved MultiBreak/SecReEvalBench and any newer equivalent contrast before a novelty assertion.

## Claims barred in this draft

No claim that adversarial history increases delayed disclosure; no claim of permanent recovery or internal memory change; no universal safer-model recommendation; no p-value, effect size, interval, significance, equivalence or ranking for the proposed pilot; no invented checker validation, human labels or plotted observations. Missing cells mean **NOT YET MEASURED** or **INSUFFICIENT VALIDATED EVIDENCE**, never zero.

## Reproducibility and format note

The editable TeX uses `IEEEtran` conference class and retains mathematical source. The DOCX is editable and uses the repository's A4 conference artifact as a style/section reference. The PDF was exported from DOCX with Microsoft Word and visually reviewed; the built-in LaTeX compiler timed out, so a TeX-compiled PDF is not claimed.

From `F:\SecureLLM`, with `TEMP` and `TMP` set to `F:\SecureLLM.tmp`:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts/verify_persisted_judge_calibration.py
& 'C:\Users\tirishaanth\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' docs/paper/build_manuscript_docx.py
```

Run `powershell -File docs/paper/build_manuscript.ps1` to regenerate the editable DOCX and Word-rendered PDF. No model inference is required to regenerate this pre-results draft.
