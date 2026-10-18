# Human review execution checkpoint

**Checkpoint date:** 2026-10-11. **Scope:** 36 blinded exploratory Phase 4 target responses, package `phase5-independent-review-v2`. No human review has been performed or represented as performed. This is an evidence ledger; change a box only when the stated artifact exists and its integrity is checked. Keep personal identities and raw submissions in restricted storage, not this public-facing checklist.

| Step | State | Evidence required before marking complete | Evidence at this checkpoint |
|---|---|---|---|
| Reviewer package distributed | [ ] Pending | Dated access/distribution log for separate A/B copies, recipient eligibility/training, and package manifest hash | Package prepared but no distribution record |
| Reviewer A completed | [ ] Pending | Returned complete A CSV, stable pseudonymous rater ID, all 36 outcomes/rationales, locked file hash | Original A form has 36 blank rows |
| Reviewer B completed | [ ] Pending | Returned complete B CSV, different rater ID, all 36 outcomes/rationales, locked file hash | Original B form has 36 blank rows |
| Disagreements identified | [ ] Pending | `prepare_phase6_adjudication.py` report plus disagreement-only context and decision template from both locked real submissions | Cannot run on blank forms |
| Adjudication completed | [ ] Pending | Third independent rater's complete decision CSV for every disagreement, no agreement rows, locked hash | Only blank adjudication template exists |
| Labels imported | [ ] Pending | Successful dry-run, reviewed provenance and agreement report, then successful `--commit` to separate annotation DB; duplicate import rejected | No imported human labels in project databases |
| Source hashes verified | [x] **Pre-handoff verified** | 36/36 observation/source, objective, blinded-row, private-map, rubric and package hashes match | `prepare_phase5_annotation.py` returned 36 blank samples and manifest SHA-256 `a01febdf5f9d5fe545cdfa3206580ed8aca2723cb456747c25245`; post-return import must verify again |
| Inter-annotator agreement computed | [ ] Pending | Five-category raw agreement, Cohen's κ when defined, confusion matrix, sample count, and both locked human forms | No human judgments; agreement undefined |
| ASR eligibility reassessed | [ ] **Post-import pending** | Complete independently reviewed final outcomes, explicit excluded counts, source/provenance validation, and claim-specific review | Current read-only report: 0 judgment rows, 0 final outcomes, ASR `blocked`; no post-label reassessment possible |

Reviewer A and B receive their separate blank forms and the three hashed rubrics, never the private join map or each other's labels. The adjudicator receives only disagreement cases after both submissions are locked. See `docs/REVIEWER_DISTRIBUTION_INSTRUCTIONS.md` and `docs/PHASE6_HUMAN_HANDOFF.md`. Do not fill forms with generated labels, infer agreement from empty forms, or convert partial/ambiguous/unavailable responses into failures.

The next command **after authentic completed A and B forms are returned** is the disagreement handoff, run from `F:\SecureLLM` with a new output directory:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& .\.venv\Scripts\python.exe scripts/prepare_phase6_adjudication.py --reviewer-a 'ABSOLUTE_PATH_TO_COMPLETED_A.csv' --reviewer-b 'ABSOLUTE_PATH_TO_COMPLETED_B.csv' --output-dir 'ABSOLUTE_NEW_RESTRICTED_HANDOFF_DIR'
```

Replace the three path arguments with the actual returned files and a directory that does not yet exist. This command validates both forms and the source/package; it does **not** import labels or infer adjudicated outcomes. The later dry-run and commit commands are in `docs/PHASE6_HUMAN_HANDOFF.md` and may be used only after genuine independent adjudication where required.
