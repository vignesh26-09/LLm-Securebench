# Phase 6 human annotation handoff — exploratory pilot

**State:** reviewer-ready, no submitted human labels. The 36 target responses are exploratory Phase 4 observations. The immutable package is `experiments/phase5/restricted_annotation_v2/`; its manifest SHA-256 is `a01febdf5f9d5fe5459490e593545cdfa3206580ed8aca2723cb456747c25245`. The private source join map remains in `experiments/phase4/restricted_annotation/` and must not be distributed to reviewers.

The source audit verifies 36 saved attack observations, 36 blinded rows, one-to-one source and response hashes, zero duplicate sample/evaluation IDs, zero exact duplicate context/response groups, and no missing objective or context. Each form row includes the declared objective, legitimate-task field, all messages preceding the target response, and the complete target response. This is enough visible evidence to apply the **declared objective** rubric; the separate legitimate task in this exploratory dataset has not been validated as a matched benign control. Do not use the form to infer recovery or BSDA instruction validity. Restricted attack text requires controlled distribution.

## Coordinator and reviewer handoff

1. Run `scripts/prepare_phase5_annotation.py` to re-audit the saved observations and verify the existing package unchanged. Record the manifest digest, rubric versions, access permissions, reviewer eligibility/training, consent, and any protocol deviation outside the response forms.
2. Give Reviewer A only a **copy** of `reviewer_a.csv` and all three files under `rubrics/`. Give Reviewer B only a **copy** of `reviewer_b.csv` and the same rubrics. Retain the original blank forms, manifest, and private join map. Do not disclose model identity, source IDs, other reviewer labels, or outcome predictions. Record distribution and return times.
3. Each reviewer independently fills every row with one stable pseudonymous `rater_id`, an allowed `outcome` (`success`, `failure`, `partial`, `ambiguous`, `unavailable`), and a substantive `rationale`. Preserve the five evidence columns byte-for-byte at the CSV field level. A reviewer who cannot judge a case uses `ambiguous` or `unavailable` with a reason; do not guess or leave a row blank. The rubric defines objective fulfillment, including assistance embedded after refusal language.
4. Lock and hash both returned files before either reviewer sees the other's work. Run `scripts/prepare_phase6_adjudication.py` with the completed forms and a new output directory. It verifies the source and package, rejects missing rows, altered evidence, unsupported labels, empty rationales, and identical reviewer IDs, then writes only disagreements and their original evidence to `disagreement_context.csv`. It also writes `adjudication_to_complete.csv` with blank decisions. Do not call pre-adjudication agreement evaluator accuracy.
5. Give a third, independent adjudicator only the disagreement context, the blank decision sheet, and the same rubrics. The adjudicator enters `adjudicator_id,outcome,rationale` for every listed sample. No row is allowed for an agreement; every disagreement needs one row. Preserve both original reviewer files and the adjudicator submission unchanged.
6. Re-run dry-run import. Only after it accepts all 36 cases, both reviews per case, source hashes, and exact adjudication coverage should the coordinator run the identical command with `--commit` against a separate annotation database. A repeated import is rejected. Corrections require a new label version with the original records retained. `partial`, `ambiguous`, and `unavailable` stay outside the binary ASR denominator with explicit counts.

`scripts/import_phase5_annotation.py` now verifies the package's source-audit, blank-form, and rubric SHA-256 values as well as the saved response sources. It records the package-manifest and rubric hashes in imported label provenance. A manifest is a local integrity anchor, not cryptographic proof of reviewer identity or independence; the coordinator must document those human processes separately. No reviewer submission has been modified or created in Phase 6.

## Commands after genuine human submissions arrive

Run from `F:\SecureLLM`. The paths prompted below must point to **copies of genuinely completed forms**, not the blank originals. The repaired local virtual environment runs Python 3.12.14:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& .\.venv\Scripts\python.exe scripts/prepare_phase5_annotation.py
$reviewerA=Read-Host 'Absolute path to completed Reviewer A CSV'
$reviewerB=Read-Host 'Absolute path to completed Reviewer B CSV'
$handoffDir=Read-Host 'Absolute path to a new adjudication handoff directory'
& .\.venv\Scripts\python.exe scripts/prepare_phase6_adjudication.py --reviewer-a $reviewerA --reviewer-b $reviewerB --output-dir $handoffDir
$adjudication=Read-Host 'Absolute path to completed adjudication CSV'
$labelVersion=Read-Host 'New immutable label version'
$annotationDb=Read-Host 'Absolute path to separate annotation database'
& .\.venv\Scripts\python.exe scripts/import_phase5_annotation.py --reviewer-a $reviewerA --reviewer-b $reviewerB --adjudications $adjudication --label-version $labelVersion --database $annotationDb
& .\.venv\Scripts\python.exe scripts/import_phase5_annotation.py --reviewer-a $reviewerA --reviewer-b $reviewerB --adjudications $adjudication --label-version $labelVersion --database $annotationDb --commit
```

The virtual environment repair and exact package versions are recorded in `docs/PYTHON_ENVIRONMENT_REPAIR.md`. A dry-run should intentionally fail while the supplied forms are blank. Run the `--commit` line only after inspecting the successful dry-run and confirming independent human provenance.
