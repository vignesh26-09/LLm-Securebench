# Phase 6 empirical-validation gate report

**Decision:** human evaluation is pending; SecureLLMBench is **not empirically validated** for model safety claims. No production calls or human labels were generated in Phase 6. The existing 100-call, two-goal Phase 4 run remains exploratory engineering/annotation evidence, not a model comparison.

## Verified evidence and annotation state

The immutable Phase 5 package re-audited successfully: 36/36 completed attack observations match their source files, declared objectives, blinded rows, and SHA-256 private mapping. The package manifest SHA-256 is `a01febdf5f9d5fe5459490e593545cdfa3206580ed8aca2723cb456747c25245`. The source audit reports zero duplicate evaluation IDs, sample IDs, or exact context/response groups; zero missing context/objectives; zero source-hash mismatches. Each blinded row includes objective, legitimate-task field, preceding conversation, and complete target response. The forms are blank. The project's three database files (`securellmbench.db`, `experiments/phase3b/pilot_v1.db`, `experiments/phase4/jbb_pilot_v1.db`) each contain **0** `human_annotation`, **0** `human_adjudication`, and **0** `attack_outcome` records. No completed reviewer submissions were found in the workspace.

The handoff is in `docs/PHASE6_HUMAN_HANDOFF.md`. Reviewer A and B receive separate form copies and the hashed rubrics; an independent adjudicator sees only disagreements after both submissions are locked. `scripts/prepare_phase6_adjudication.py` creates a disagreement-only context sheet and blank decision sheet in a new directory, without modifying reviewer files. The importer requires complete source-exact forms, two distinct raters, every disagreement adjudicated by a different person, legal outcomes/rationales, and unaltered source hashes. It now checks the versioned package/rubric hashes and records them in imported provenance. Dry-run with the existing blank forms correctly rejects the missing reviewer ID and creates no annotation database. Synthetic test fixtures demonstrate disagreement rejection, separate adjudication, null-preserving partial outcomes, provenance, duplicate-import rejection, and package tamper rejection; they are **not human evidence**.

## Scientific eligibility

| Item | Current status | Reason |
|---|---|
| Independent human records | **0/36** | No actual reviewer submissions. |
| Adjudicated records | **0** | No human disagreements to adjudicate. |
| ASR | **Blocked** | No complete independent final outcome set; partial database rows cannot unlock the report. |
| BSDA | **Uncalibrated** | Versioned validated representations, component bounds, and a justified legitimate-task control are absent. |
| Recovery capability | **Undefined** | Behavioral states, positive floor, and valid recovery probes are absent. |
| SAEA | **Blocked** | Validated states and provider-level isolation evidence are absent; matched delta cannot be inferred from calls alone. |
| Historical Gemma safety-stance evaluator | **Unvalidated for jailbreak success** | Historical 300-row calibration has 295 usable, TN=51, FP=135, FN=1, TP=108, agreement 53.898%, κ=0.21126; it answers a different claim and has high false-positive count. |
| New evaluator comparison | **Pending** | No independently labeled held-out target responses or frozen test split. |
| Model ranking / selection | **Blocked** | No validated outcome/behavioral measurements or uncertainty basis. |

Claim-specific evaluator statistics, probability-calibration limits, intervals, and subgroup analysis are specified in `docs/PHASE6_VALIDATION_GATES.md`. No threshold was tuned on test data; no historical comparator column was treated as a new evaluator run.

## Production proposal and freeze

The pinned-source audit still yields **66** candidate goals across ten categories after excluding 13 lexical near-overlaps with historical calibration and two used pilot goals. Within the candidates it finds no exact duplicate or ≥0.90 lexical near-duplicate pairs; semantic/rights review remains outstanding. Proposed split: 10 development, 16 validation, 40 untouched test, with source-goal grouping and exact IDs **not frozen**. Proposed two models are historical local `qwen3.5:2b` and `gemma3:4b` digests from Phase 4; recheck identities before a new run. One trajectory per 66 goals/models plus ten complete repeated goal groups gives a **3,800-call cap**, up to 1,368 attack responses and 2,736 initial independent judgments. This is a feasibility envelope, not a powered design. Matched benign tasks, recovery probes, representation calibration, effect/precision target, semantic split review, isolation strategy, current model identities, reviewer staffing, and analysis multiplicity/stop rules must be resolved before an append-only production lock. `docs/PHASE6_PRODUCTION_PROPOSAL.md` contains the conditions, analysis and exclusions. No confirmatory protocol was frozen; no expensive production experiment was started.

## Verification and environment

The full Python suite passed **215 tests, 1 dependency deprecation warning**. The real-package re-audit passed with 36 blank forms. Persisted judge calibration verification returned source N=300, usable N=295, coverage=98.333%, agreement=53.898%, κ=0.2112609601698581 and the matrix above, source SHA-256 `dacaf76a1057785f11b0fc6aa07b9a73cdab588319ddfc5e8cef2909e5b112a5`. API smoke passed health/ready (200), review creation (201), and eight read-resource checks; the smoke explicitly reported `scientific_claims_validated=False`. The blank-form import negative test passed. No frontend work was required for this backend-only scientific gate.

The local `.venv\Scripts\python.exe` launcher was repaired in place on 2026-10-11 using the available Python 3.12.14 base; all 43 installed distribution versions were preserved. `py -3.12` still points to a missing system executable, so use the project venv explicitly. Repair evidence is in `docs/PYTHON_ENVIRONMENT_REPAIR.md`. For exact current-environment checks from `F:\SecureLLM`:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& .\.venv\Scripts\python.exe scripts/prepare_phase5_annotation.py
& .\.venv\Scripts\python.exe scripts/verify_persisted_judge_calibration.py
& .\.venv\Scripts\python.exe scripts/api_smoke.py
& .\.venv\Scripts\python.exe -m pytest -q
```

**Next research operation:** recruit two independent qualified reviewers and a separate adjudicator; record training, consent, eligibility, blinding, access, and submission hashes; distribute the already-audited package without the private join map. Once genuinely completed forms arrive, use the commands in `docs/PHASE6_HUMAN_HANDOFF.md` to prepare disagreement review, dry-run import, and only then commit a new label version. After that, report inter-annotator agreement and assess claim-specific evaluator and metric eligibility. External human labor, validation data/control design, provider isolation evidence, model/hardware capacity, and a predeclared precision target remain dependencies. Do not state empirical validation or a safer-model conclusion before these gates pass.
