# Phase 5 research-readiness decision

**Decision (11 October 2026): reviewer-ready and traceable; independent empirical validation is still blocked by absent human raters and behavioral-measurement validation.** The 36 exported samples were verified one-to-one against saved Phase 4 observations, source hashes, histories, and predeclared objectives. The self-contained `experiments/phase5/restricted_annotation_v2/` package has two blank reviewer forms, an adjudication template, versioned rubric copies, and an immutable manifest. The package itself contains zero labels.

| Gate | Result | Decision |
|---|---|---|
| Real-source execution | 100 completed Phase 4 calls, 36 completed attack responses, source/model/protocol provenance. | Exploratory execution available. |
| Annotation transport | 36/36 source matches; no duplicate IDs, missing histories/objectives, or hash mismatches. | Reviewer-ready. |
| Independent human reference | Two genuine raters and independent adjudicator have not supplied any judgments. | ASR, agreement, and judge comparison blocked. |
| Import enforcement | Blank/duplicate/tampered forms and missing adjudication are rejected in synthetic tests; source hashes and append-only IDs checked. | Software workflow testable, not evidence of real annotation quality. |
| Behavioral measurements | No validated state representation, component calibration, separate legitimate task, or valid recovery probe. | BSDA uncalibrated; RC undefined; SAEA blocked. |
| Isolation/context | Histories consistent; 24 pilot isolated-control ledger entries provider-unverifiable. | No verified session independence claim. |
| Evaluator | Historical Gemma stance calibration κ≈0.211; official comparator columns are stored historical predictions. | No eligible automated sole truth. |
| Production | Conditional 3,800-call/2,736-judgment cap and 66-goal pool proposed, but exact splits, precision for paired effects, rater capacity, and validation are not frozen. | Do not execute expensive confirmatory study. |

The next human dependency is two qualified independent reviewers to complete the restricted 36-row forms, followed by a third-party adjudicator for disagreements. Their actual labels would permit pre-adjudication agreement and exploratory human-labeled outcomes, but would **not by themselves** validate BSDA/RC/SAEA, make the pilot held-out, or justify a model-safety ranking. Subsequent gates are claim-specific evaluator validation, behavioral-state calibration, matched benign/recovery-task validation, and an append-only frozen production protocol. A paper can describe the research software, evidence controls, real-source feasibility, and the separate historical judge-calibration negative result; it cannot yet claim novel validated behavioral safety findings or recommend one model over another.

Verification on 11 October 2026: **212 Python tests passed, 0 failed**, with one existing Starlette/httpx deprecation warning. The Phase 5 tests include real-artifact source/manifest audits, blank-form rejection, and clearly marked synthetic form/adjudication/duplicate-import cases. The reviewer-package CLI reproduced its immutable SHA-256 manifest; the eligibility report found 100 observations, 36 attack responses, zero human labels, and zero validated safety metrics. API smoke passed health/ready (HTTP 200), eight read resources, and a fixture review write (HTTP 201). The persisted historical calibration verifier reproduced 300 source/295 usable, TN=51, FP=135, FN=1, TP=108, coverage 98.33%, raw agreement 53.90%, and κ=0.211261. `git diff --check` returned no whitespace errors. These are software/provenance checks, not evidence of human validation.

## Reproduction without model calls

From PowerShell in `F:\SecureLLM`, use the specified interpreter and set `$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'` for the session. The following commands recheck sources, package, measurement eligibility, and regressions without creating judgments:

```powershell
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\prepare_phase5_annotation.py
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\report_phase5_measurement_eligibility.py --output experiments\phase5\measurement_eligibility_v1.json
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\report_phase5_source_pool.py --output experiments\phase5\production_source_pool_v1.json
& 'F:\SecureLLM\.venv\Scripts\python.exe' -m pytest -q
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\api_smoke.py
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\verify_persisted_judge_calibration.py
```

Once two real reviewers return completed forms and independent adjudication is finished, validate with `scripts\import_phase5_annotation.py --reviewer-a FORM_A --reviewer-b FORM_B --adjudications ADJUDICATIONS --label-version NEW_VERSION --database experiments\phase5\annotation_labels_v1.db`; add `--commit` only after the validation report is reviewed. The blank distributed templates deliberately fail import. Repeat imports and changed source hashes are rejected. Preserve the private join map and completed forms in restricted storage.
