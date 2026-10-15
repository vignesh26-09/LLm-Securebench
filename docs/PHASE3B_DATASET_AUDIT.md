# Phase 3B dataset and access audit (10 October 2026)

## What is actually local

| Artifact | Identity and role | Eligibility for new attack-execution research |
|---|---|---|
| `data/raw/example.json` | Three-case dashboard/engineering demonstration; two prompts are closely related. | No: no approved attack objectives, split, independent labels, or research sampling design. |
| `data/external/jailbreakbench_judge_comparison_b2b462fd.csv` | 300 historical response-and-judge-comparison rows; SHA-256 `dacaf76a1057785f11b0fc6aa07b9a73cdab588319ddfc5e8cef2909e5b112a5`. | Evaluator diagnostics only. These are not new responses from the two local target models and cannot silently become Phase 3B attack cases. |
| `experiments/phase3b/pilot_dataset_v1.json` | One author-created harmless instruction-following case; SHA-256 `02bbb015288b088412d9802ee223c9d852789a6d60a978ee09ba6270f6ab96fa`. | Engineering pilot only. The three "attacks" are synthetic formatting overrides, not cybersecurity or safety outcomes. No research split or external benchmark claim. |

No source-controlled, licensed, case-selected Phase 3B target-execution dataset with independently declared legitimate tasks, attack objectives, attack-family annotations, and frozen related-group splits is present. No benchmark dataset or model weights were downloaded in this pass.

## Candidate sources; selection remains open

- [JailbreakBench official repository](https://github.com/JailbreakBench/jailbreakbench) documents its harmful and benign behavior resources and evaluation conventions. The [JBB-Behaviors license file](https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/blob/main/LICENSE) is MIT. A future study must pin the exact behavior revision and separately review any imported attack artifact's rights, objectives, and suitability. Its historical judge-comparison CSV is a different artifact.
- [HarmBench official repository](https://github.com/centerforaisafety/HarmBench) provides standardized adversarial behavior/evaluation resources and MIT-licensed code. Its reference classifier and workflows carry hardware/installation costs; neither was installed or executed here. Constituent data rights and exact revisions still need a separate manifest.
- [MT-JailBench official repository](https://github.com/SafetyArena/mt-jailbench) is a multi-turn candidate with MIT-licensed code. It is not local, and its provider-dependent procedures cannot be presumed equivalent to this runner's sequential-versus-isolated estimand. Attack content, rights, split grouping, and case objectives need review before import.

## Implemented integrity checks

`core/experiments/execution_gate.py` verifies actual dataset bytes against the specification SHA-256, dataset ID/version, unique case IDs, and exact case content before any target call. `core/experiments/dataset_audit.py` validates future research manifest provenance, source revision/license/checksum, explicit legitimate task and attack objective/category, unique IDs, development/validation/test split fields, declared related-group isolation, and exact cross-split duplicate rejection. Lexical near duplicates across splits are flagged for manual review; this heuristic is not a semantic-leakage guarantee. The existing `core/evaluation/split_integrity.py` separately guards evaluator reference splits.

The pilot uses `pilot_only_no_research_split` and is deliberately ineligible for research analysis. A production manifest must be prepared from a legitimately accessed source and pass these checks before a locally frozen confirmatory protocol can be established. No missing attack-family labels were inferred from historical response text.
