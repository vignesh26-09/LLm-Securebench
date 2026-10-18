# Public readiness audit

Read-only evidence audit of public-clean at 76806d5; no network requests, model calls, or licence lookups were made.
Licence names below reproduce local statements only. They do not establish rights to every constituent prompt, response, or derivative.

## External datasets

Only data/external/.gitkeep is tracked under data/external. Original external dataset bytes and local upstream LICENSE files are not tracked.

| Source | Bytes in public-clean | Locally stated upstream licence | Local evidence |
|---|---|---|---|
| Databricks Dolly 15k | Source file untracked; acquisition script and corpus manifest tracked | CC-BY-SA-3.0 | scripts/build_10000_corpus.py:28; data/benchmark_10000.manifest.json |
| Anthropic hh-rlhf red-team attempts | Source archive untracked; acquisition script and corpus manifest tracked | MIT (repository metadata) | scripts/build_10000_corpus.py:35; data/benchmark_10000.manifest.json |
| JailbreakBench historical judge-comparison CSV | CSV and its local manifest untracked; diagnostic scripts/docs tracked | MIT, as recorded for the JailbreakBench repository | data/external/jailbreakbench_judge_comparison_b2b462fd.manifest.json, license_evidence field |
| JailbreakBench JBB-Behaviors | Pinned directory untracked; fetch/manifest scripts tracked | MIT | Local data/external/jbb_behaviors_886acc3/LICENSE; scripts/build_phase4_dataset_manifest.py:34 |
| JailbreakBench attack artifacts | Pinned directory untracked; fetch/manifest scripts tracked | MIT | Local data/external/jbb_artifacts_909e68c/LICENSE; scripts/build_phase4_dataset_manifest.py:35 |

Sources with no locally stated upstream licence (UNKNOWN): 0 of 5.
No original external source files are tracked; selected derived paper artifacts and example traces elsewhere in the repository remain tracked.
The root software LICENSE does not replace upstream dataset terms. Constituent rights, attribution, share-alike conditions, and redistribution rights require manual review.

## README claims

Unqualified overclaim lines found: 0. The scan checked standalone validated, proven, secure, and state-of-the-art wording, excluding the project brand name.
Qualified matches: README.md:51 explicitly denies scientific validation; README.md:63 denies preset-model validation claims; README.md:67 denies a security-ranking claim.
Existing README.md:126-146 describes small models, low V0 recall, LLM-only annotation, a retrospective split/no fresh holdout, and oracle limitations.
These existing qualifications are not evidence of production suitability. Manual editorial review is still required.

## Commit-author privacy and identity

Commits audited: 3. Commits whose author email is a placeholder: 3. No email values are reproduced.
Placeholder classification includes example/test/invalid/local domains, missing fully qualified domains, and generic placeholder local parts.
This count describes the pre-audit HEAD above; creating this audit's commit may add another commit under the current unchanged identity.
No author identity, credentials, configuration, or history was changed.

## Local blinded review kit

Source: 120 previously LLM-annotated rows; no new model outputs or annotations were generated.
Selection seed: 42; selected 30 rows, including 15 non-safe candidates and 8 judge/LLM-reference disagreements.
Selection first takes up to 15 candidates flagged by the judge or any LLM annotator, preferring judge/reference disagreement, then samples the remaining rows randomly from non-candidates.
Set 1 reference: two-pass majority, ties borderline. Set 2 reference: saved three-annotator majority, with no majority mapped to borderline.
The sheet contains only id, prompt, model_output, blank label and blank notes; the separate key contains model/judge/LLM-reference information.
The kit is local and gitignored. Keep the key hidden from the reviewer. Existing source sheets and annotations were not modified.
No completed human labels or human-validation result is claimed. Scoring refuses blank/invalid labels and writes its report only after all 30 are complete.
Oversampling flagged/disputed cases means agreement and Wilson intervals apply to this selected small sample, not the full output population.

## Manual checklist before making the repository public

- Verify all five upstream dataset licences, versions, notices, and constituent/derived-data redistribution rights.
- Set an appropriate real or GitHub privacy-protected author email for future commits; decide how to handle existing placeholder authors separately.
- Review README claims and paper artifacts against actual evidence and their limitations.
- Keep the repository's GitHub Private badge until these reviews are complete; privacy was not checked over the network.
- Obtain independent completed labels using the blinded sheet without showing the key or LLM annotations.
- Run scripts/score_human_labels.py on the local kit only after all 30 labels are complete.
- Keep local databases, source downloads, outputs, and the review kit out of every staged/public snapshot.
