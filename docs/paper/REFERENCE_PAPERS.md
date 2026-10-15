# Reference Papers for the SecureLLMBench IEEE Manuscript

## Recommended core literature set

These papers directly support the motivation, design choices, evaluator-validation discussion, and threat model of SecureLLMBench. Prefer this focused set over a long bibliography containing weakly related work.

## A. Standardized jailbreak and red-team evaluation

### [1] JailbreakBench

P. Chao *et al.*, “JailbreakBench: An open robustness benchmark for jailbreaking large language models,” in *Advances in Neural Information Processing Systems*, vol. 37, 2024, doi: [10.52202/079017-1745](https://doi.org/10.52202/079017-1745).

Official paper: [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/63092d79154adebd7305dfd498cbff70-Abstract-Datasets_and_Benchmarks_Track.html)

Use it to support:

- the need for standardized threat models, prompts, chat templates, and scoring;
- the reproducibility problem caused by private prompts or changing APIs;
- the observation that attack costs and success rates are often incomparable.

Suggested sentence:

> JailbreakBench identifies inconsistent success definitions, unreleased attack artifacts, and changing proprietary interfaces as barriers to reproducible jailbreak evaluation [1].

### [2] HarmBench

M. Mazeika *et al.*, “HarmBench: A standardized evaluation framework for automated red teaming and robust refusal,” in *Proc. 41st Int. Conf. Machine Learning*, ser. Proceedings of Machine Learning Research, vol. 235, pp. 35181–35224, 2024.

Official paper: [PMLR](https://proceedings.mlr.press/v235/mazeika24a.html)

Use it to support:

- standardized automated red-team evaluation;
- evaluation across multiple attack and defense methods;
- the need to measure both adversarial success and robust refusal.

Suggested sentence:

> HarmBench demonstrates the value of a standardized evaluation framework spanning attacks, target models, and defenses [2].

### [3] StrongREJECT

A. Souly *et al.*, “A StrongREJECT for empty jailbreaks,” in *Advances in Neural Information Processing Systems*, vol. 37, 2024, doi: [10.52202/079017-3984](https://doi.org/10.52202/079017-3984).

Official paper: [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/e2e06adf560b0706d3b1ddfca9f29756-Abstract-Datasets_and_Benchmarks_Track.html)

Use it to support:

- why superficial refusal bypass is not sufficient evidence of harmful usefulness;
- why automated jailbreak evaluators must be compared with human judgments;
- why reported attack-success rates can be overstated.

Suggested sentence:

> StrongREJECT shows that several evaluation procedures overstate jailbreak effectiveness relative to human judgments, motivating outcome definitions that measure useful harmful content rather than superficial refusal bypass [3].

## B. Prompt injection and agent-security benchmarks

### [4] AgentDojo

E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer, and F. Tramèr, “AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,” in *Advances in Neural Information Processing Systems*, vol. 37, 2024, doi: [10.52202/079017-2636](https://doi.org/10.52202/079017-2636).

Official paper: [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html)

Use it to support:

- the threat of untrusted data returned by tools;
- the need to evaluate task utility as well as security;
- realistic agent tasks and adaptive attacks.

### [5] InjecAgent

Q. Zhan, Z. Liang, Z. Ying, and D. Kang, “InjecAgent: Benchmarking indirect prompt injections in tool-integrated large language model agents,” in *Findings of the Association for Computational Linguistics: ACL 2024*, pp. 10471–10506, 2024, doi: [10.18653/v1/2024.findings-acl.624](https://doi.org/10.18653/v1/2024.findings-acl.624).

Official paper: [ACL Anthology](https://aclanthology.org/2024.findings-acl.624/)

Use it to support:

- indirect prompt injection through external content;
- direct-harm and private-data-exfiltration threat categories;
- benchmark construction for tool-integrated agents.

Suggested combined sentence:

> AgentDojo and InjecAgent extend language-model security evaluation to tool-integrated systems in which untrusted external content may redirect agent behavior or cause data exfiltration [4], [5].

## C. Conversation history and context position

### [6] Lost in the Middle

N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, “Lost in the middle: How language models use long contexts,” *Transactions of the Association for Computational Linguistics*, vol. 12, pp. 157–173, 2024, doi: [10.1162/tacl_a_00638](https://doi.org/10.1162/tacl_a_00638).

Official paper: [ACL Anthology](https://aclanthology.org/2024.tacl-1.9/)

Use it to support:

- the claim that information position can affect model behavior;
- the motivation for testing prompt distance and conversation history;
- the requirement for controlled positional comparisons.

Evidence boundary:

This paper studies long-context information use, not jailbreak persistence. Cite it as motivation for controlled context-position experiments, not as proof that delayed adversarial effects exist.

## D. Automated judges and evaluator validity

### [7] MT-Bench and Chatbot Arena judge study

L. Zheng *et al.*, “Judging LLM-as-a-judge with MT-Bench and Chatbot Arena,” in *Advances in Neural Information Processing Systems*, vol. 36, 2023, doi: [10.52202/075280-2020](https://doi.org/10.52202/075280-2020).

Official paper: [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html)

Use it to support:

- the potential scalability of language models as evaluators;
- known position, verbosity, self-enhancement, and reasoning biases;
- comparison of judge behavior with human preferences.

### [8] G-Eval

Y. Liu, D. Iter, Y. Xu, S. Wang, R. Xu, and C. Zhu, “G-Eval: NLG evaluation using GPT-4 with better human alignment,” in *Proc. 2023 Conf. Empirical Methods in Natural Language Processing*, pp. 2511–2522, 2023, doi: [10.18653/v1/2023.emnlp-main.153](https://doi.org/10.18653/v1/2023.emnlp-main.153).

Official paper: [ACL Anthology](https://aclanthology.org/2023.emnlp-main.153/)

Use it to support:

- structured form-based language-model evaluation;
- comparison between automated ratings and human judgments;
- the possibility of evaluator bias toward model-generated text.

### [9] A Closer Look into Automatic Evaluation

C.-H. Chiang and H.-Y. Lee, “A closer look into using large language models for automatic evaluation,” in *Findings of the Association for Computational Linguistics: EMNLP 2023*, pp. 8928–8942, 2023, doi: [10.18653/v1/2023.findings-emnlp.599](https://doi.org/10.18653/v1/2023.findings-emnlp.599).

Official paper: [ACL Anthology](https://aclanthology.org/2023.findings-emnlp.599/)

Use it to support:

- sensitivity of judge quality to prompting and output format;
- the need to preserve evaluator configuration;
- why an evaluator implementation should not be treated as universally valid.

### [10] Human and LLM judgment bias

G. H. Chen, S. Chen, Z. Liu, F. Jiang, and B. Wang, “Humans or LLMs as the judge? A study on judgement bias,” in *Proc. 2024 Conf. Empirical Methods in Natural Language Processing*, pp. 8301–8327, 2024, doi: [10.18653/v1/2024.emnlp-main.474](https://doi.org/10.18653/v1/2024.emnlp-main.474).

Official paper: [ACL Anthology](https://aclanthology.org/2024.emnlp-main.474/)

Use it to support:

- the presence of bias and vulnerability in human and model judges;
- the need for robust evaluator-validation procedures;
- the argument that judge outputs must retain provenance.

Suggested paragraph:

> Language-model judges can reduce evaluation cost and have shown useful correspondence with human preferences in some settings [7], [8]. However, their results depend on prompt construction, requested output format, model identity, and task [9], and both human and model judges may exhibit systematic biases [10]. SecureLLMBench therefore records evaluator provenance and requires task-specific calibration before judge labels are promoted to benchmark outcomes.

## E. Agreement statistic

### [11] Cohen's kappa

J. Cohen, “A coefficient of agreement for nominal scales,” *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960, doi: [10.1177/001316446002000104](https://doi.org/10.1177/001316446002000104).

Official paper: [SAGE Journals](https://journals.sagepub.com/doi/abs/10.1177/001316446002000104)

Use it to support:

- the definition of chance-corrected agreement;
- equation (3) in the manuscript;
- reporting kappa alongside raw agreement and the confusion matrix.

Do not use a universal verbal label such as “fair” as the sole interpretation. Report the numerical value, class distribution, confusion counts, and task context.

---

## Citation placement by paper section

| IEEE section | References | Purpose |
|---|---|---|
| I. Introduction | [1]–[3], [7], [10] | Establish benchmark inconsistency and evaluator-validity problem |
| II-A. Jailbreak benchmarks | [1]–[3] | Compare standardized datasets, threats, and outcome scoring |
| II-B. Prompt injection | [4], [5] | Define tool and untrusted-content threat settings |
| II-C. Context effects | [6] | Motivate controlled prompt-position and history tests |
| II-D. Automated judges | [7]–[10] | Balance benefits with known biases and sensitivity |
| III-E. Metric eligibility | [11] | Define Cohen's kappa |
| IV-B. Judge calibration | [7]–[11] | Interpret the local agreement result relative to evaluator literature |

## Most important comparisons to explain

### SecureLLMBench versus JailbreakBench and HarmBench

JailbreakBench and HarmBench primarily standardize benchmark content and evaluation across attacks, models, and defenses. SecureLLMBench should be positioned as complementary infrastructure emphasizing evidence lineage, unavailable-result states, evaluator calibration, and claim gating.

### SecureLLMBench versus StrongREJECT

StrongREJECT provides a dataset and evaluator intended to better measure useful harmfulness. SecureLLMBench does not currently claim a superior jailbreak-success evaluator. Its distinct role is preserving multiple evidence layers and refusing to expose an unvalidated evaluator as ground truth.

### SecureLLMBench versus AgentDojo and InjecAgent

AgentDojo and InjecAgent focus on tool-integrated agents and indirect prompt injection. SecureLLMBench currently provides a more general evaluation workflow and does not reproduce their complete agent environments. Cite them to define adjacent threat models, not to claim feature equivalence.

### SecureLLMBench versus LLM-as-a-judge frameworks

MT-Bench, G-Eval, and related studies show that language-model judging can be useful. The SecureLLMBench calibration result demonstrates why usefulness must be established for the exact task and configuration. The paper should present this as task-specific validation, not a rejection of all automated judges.

## Reference-quality rules

- Cite the final publisher or conference record instead of a blog post.
- Prefer the DOI link where one exists.
- Use the arXiv version only when no archival version is available.
- Verify author order, title capitalization, pages, venue, year, and DOI before submission.
- Number references by first appearance in the final manuscript; the numbering above is a recommended order, not a permanent identifier.
- Do not cite a paper for a stronger statement than it actually establishes.
- Keep dataset, code, and benchmark websites as supplementary URLs when the archival paper already exists.

