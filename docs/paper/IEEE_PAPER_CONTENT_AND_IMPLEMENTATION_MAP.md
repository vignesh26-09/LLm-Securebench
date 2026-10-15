# SecureLLMBench: IEEE Paper Content and Implementation Map

## 1. Recommended paper position

This paper should be presented as a **research-software and validation methodology paper**, not as a completed claim that one language model is safer than another.

Target submission title:

> **SecureLLMBench: A Traceable and Validation-Aware Platform for Reproducible LLM Security Evaluation**

This title describes the platform itself and matches the strongest evidence currently available. “Traceable” reflects the linked dataset, configuration, inference, evidence, and report records. “Validation-aware” reflects the explicit available, unavailable, uncalibrated, and blocked metric states. “Reproducible” reflects versioned inputs, provider metadata, execution traces, and exportable artifacts. The title does not depend on an unfinished human-validation study or restrict the platform to only small open-weight models.

The current implementation already provides the supporting infrastructure:

- the framework records benchmark inputs, configurations, outputs, detector evidence, evaluation records, and validation state;
- unsupported metrics are kept unavailable instead of being silently converted into scores;
- the repository contains a completed external judge-calibration analysis;
- local Qwen and Gemma runs demonstrate execution and reporting, but they are too small and insufficiently labeled for safety conclusions.

The earlier study-specific titles—*SecureLLMBench: Control-Adjusted Evaluation of Adversarial Conversation History and Delayed Security-Policy Violations in Large Language Models* and *SecureLLMBench: Human-Validated Security Scoring and Post-Attack Reliability Drift in Small Open-Weight LLMs*—should be reserved for a future empirical paper after the delayed-disclosure experiment is implemented, frozen, executed, independently labeled, and statistically analyzed.

---

## 2. What has been implemented

### A. Dataset and provenance layer

Implemented:

- ingestion of JSON, JSONL, and CSV datasets;
- dataset-version records and checksums;
- case-level identifiers and metadata;
- optional semantic data-quality inspection;
- traceability from a benchmark run back to its dataset version and configuration.

How it works:

1. A dataset is imported and normalized into benchmark cases.
2. A version record identifies the exact data used in a run.
3. Checksums and identifiers make accidental dataset drift detectable.
4. The benchmark configuration references the frozen version rather than an informal filename.

Paper-safe claim:

> SecureLLMBench provides versioned dataset ingestion and provenance records for reconstructing the inputs used by a benchmark run.

Do not claim that the current datasets are representative of all jailbreaks, domains, languages, or production threats.

### B. Model registry and inference layer

Implemented:

- provider-neutral model and inference contracts;
- mock inference for deterministic tests;
- local Ollama integration;
- opt-in OpenAI-compatible endpoints;
- Transformers-based inference support;
- model identity, provider, generation settings, latency, and response recording.

How it works:

1. The registry stores a model identity and provider configuration.
2. A benchmark run resolves that identity through a provider adapter.
3. Each case is rendered into a prompt or conversation and sent to the provider.
4. The returned text, timing, model metadata, and execution status are persisted.
5. Provider failures remain explicit instead of being counted as safe responses.

Paper-safe claim:

> A common provider contract allows the same benchmark workflow to run against mock, local, and compatible remote inference backends while preserving execution metadata.

### C. Benchmark execution and storage

Implemented:

- benchmark configuration and execution records;
- per-case evaluation storage;
- response traces and operational metadata;
- SQLAlchemy persistence;
- FastAPI endpoints;
- explicit run status and failure records;
- scientific-record and model-score storage.

How it works:

1. The runner loads a versioned dataset and model configuration.
2. It executes each case and stores the raw response.
3. Detection and evaluation stages create linked evidence records.
4. Run-level summaries are calculated only from eligible records.
5. API endpoints expose the stored records to the dashboard and report exporters.

### D. Layer 1 deterministic detection

Implemented:

- keyword, regular-expression, and pattern-based detectors;
- detector-level evidence records;
- matched-signal counts and rule identifiers;
- aggregation into descriptive threat indicators.

How it works:

1. Each model response is evaluated by deterministic rules.
2. A rule match creates an auditable evidence item.
3. Rule evidence is aggregated for descriptive dashboards.
4. These matches are not automatically treated as ground-truth jailbreak success.

Paper-safe claim:

> The first evaluation layer records reproducible lexical and pattern evidence for every response.

Do not claim:

> A Layer 1 match proves that a response is harmful, unsafe, or successfully jailbroken.

### E. Layer 2 judge orchestration

Implemented:

- structured judge contracts;
- judge request and result schemas;
- mock judge support;
- local Ollama judge support;
- coverage and failure accounting;
- calibration analysis against external labels.

How it works:

1. An eligible response is sent to a configured judge with a structured rubric.
2. The framework records the returned label, rationale, execution status, and provenance.
3. Missing or failed judgments are excluded and reported through coverage rather than silently assigned a class.
4. Agreement with independent labels is measured before the judge is accepted as an outcome evaluator.

Completed calibration evidence:

- comparison records: 300;
- usable paired judgments: 295;
- coverage: 98.333%;
- fixed-label agreement: 53.898%;
- Cohen's kappa: 0.211261;
- confusion counts: predicted 0/human 0 = 51, predicted 0/human 1 = 1, predicted 1/human 0 = 135, predicted 1/human 1 = 108.

Interpretation:

> The judge produced high coverage but weak-to-fair agreement after chance correction. It is therefore not validated as a substitute for independent human labels in the current configuration.

### F. Metric contracts

Implemented as schemas, calculators, validation gates, or descriptive components:

1. **Attack Success Rate (ASR)**

   \[
   \mathrm{ASR}=\frac{N_{\mathrm{successful}}}{N_{\mathrm{classified}}}.
   \tag{1}
   \]

   Only responses with an explicit valid outcome belong in the denominator. Missing, failed, or unclassified records are reported separately. If no valid outcome exists, ASR is undefined rather than zero.

2. **Behavioral Safety Degradation Assessment (BSDA)**

   Four component families are represented: semantic, safety, instruction-following, and structural measurements. A scientifically validated composite BSDA score has not been established.

3. **Response Consistency (RC)**

   The design supports distances between response-state representations over a trajectory and an area-under-curve summary. RC remains unavailable when states are missing, incompatible, or uncalibrated.

4. **Sequential Attack Effect Amplification (SAEA)**

   The design compares a sequential state with a matched isolated state under identity, context, and contamination gates. A valid SAEA estimate requires genuinely comparable states.

5. **Dynamic Risk and Attack Assessment (DRAA)**

   Modes A and B and their evidence profiles exist, but the scalar `risk_score` is intentionally undefined.

6. **Prompt Risk Index (PRI)**

   Modes A and B and their evidence profiles exist, but the scalar `scalar_pri` is intentionally undefined.

7. **Operational metrics**

   Coverage, latency, provider failures, token usage where available, and execution status are reportable now.

Core methodological safeguard:

> A metric is emitted only when its prerequisites and validation state are satisfied; otherwise the framework records an explicit unavailable, blocked, or uncalibrated state.

### G. Statistical and machine-learning infrastructure

Implemented:

- descriptive summaries;
- correlation and rank-based analysis utilities;
- bootstrap utilities;
- parametric-analysis utilities;
- group-aware split infrastructure;
- leakage checks;
- train-only preprocessing contracts;
- baseline-model plumbing.

Current evidence boundary:

- these components demonstrate analytical readiness;
- they do not establish predictive performance;
- no paper claim about a trained risk predictor is currently supported;
- no held-out, independently labeled test result is currently available.

### H. Dashboard and reporting

Implemented:

- a one-page scrollable research dashboard;
- live counts from the local API;
- KPI cards;
- a donut chart with a live center total;
- model-comparison cards and compact visual summaries;
- mixed-size widget layout;
- orange and muted blue design tokens;
- responsive presentation;
- a Python report exporter for paper-ready plots;
- plain-language explanations embedded in the generated charts.

React Bits Pro integration status:

- `components.json` contains the registry configuration and uses the `REACTBITS_LICENSE_KEY` environment variable for authorization;
- the Analytics 5 and Dashboard 3 packages were not fetched because a license key was not available in the environment;
- equivalent project-native dashboard functionality was implemented and adapted to the existing application;
- after the license key is supplied, the official blocks can be installed and reconciled with the current layout.

Latest local illustrative run:

| Model | Cases | Detector metric | Mean threat | Worst threat | Mean latency | Keyword signals |
|---|---:|---:|---:|---:|---:|---:|
| Qwen 3.5 2B | 3 | 86.67% | 13.33% | 20.00% | 19.14 s | 2 |
| Gemma 3 4B | 3 | 86.67% | 13.33% | 20.00% | 13.75 s | 2 |

Interpretation:

- Plot 1 shows that the two models tied on all three detector-derived metrics.
- Plot 2 shows that Gemma completed this small run faster on average.
- Plot 3 shows two keyword-rule signals for each model.
- These results describe three local cases only. They are not a statistically valid safety ranking.

Generated figures:

- `artifacts/local_metrics_report/01_metric_comparison.png`
- `artifacts/local_metrics_report/02_latency_behavior.png`
- `artifacts/local_metrics_report/03_detector_profile.png`

### I. Software verification

Observed during the dashboard work:

- frontend build passed;
- frontend lint passed;
- frontend type checking passed;
- frontend test suite passed: 9 test files and 22 tests;
- the repository currently contains 265 Python test-function definitions, but this count is not evidence that the complete Python suite passed in the latest session.

Paper-safe wording:

> The dashboard build, static checks, and frontend tests passed in the reported development environment. The number of Python test definitions is reported separately and must not be described as a passing-suite count without a fresh complete test run.

---

## 3. What is planned but not yet scientifically completed

### A. Independent human annotation

Planned:

- blinded independent reviewers;
- reviewer instructions and forms;
- adjudication of disagreement;
- explicit outcome labels;
- audit of label completeness and conflicts.

Current state:

- annotation candidates and forms exist;
- the audited production databases contain zero completed human annotations, zero adjudications, and zero accepted outcome labels;
- ASR and safety-ranking claims are therefore blocked.

### B. Evaluator validation

Planned:

- development, validation, and held-out test partitions;
- calibration against independent human labels;
- prespecified agreement, class-wise performance, and coverage thresholds;
- failure and sensitivity analyses;
- evaluator acceptance or rejection gate.

Current state:

- the existing Gemma judge failed to show sufficient agreement for replacing human labels;
- a judge may still be reported as an evaluated component, but not treated as ground truth.

### C. Controlled multi-model study

Planned requirements:

- freeze the source dataset and checksums;
- freeze model identities and revisions;
- freeze attack families, prompt order, seeds, generation settings, and repetitions;
- use independent outcome labels;
- preserve benign and isolated controls;
- run paired statistical inference;
- publish the run manifest and exclusions.

Current state:

- no completed controlled, independently labeled, repeated multi-model study exists;
- current local Qwen/Gemma observations are engineering demonstrations only.

### D. Behavioral-state validation

Planned:

- define and validate semantic, safety, instruction, and structural state representations;
- demonstrate that state distances are meaningful and reproducible;
- calibrate thresholds;
- verify identity and context comparability;
- run sequential-versus-isolated comparisons.

Current state:

- BSDA, RC, and SAEA structures exist;
- their empirical novelty and effectiveness remain unvalidated;
- Layer 1 signal counts must not be substituted for behavioral-state measurements.

### E. Scalar DRAA and PRI definitions

Planned:

- establish a theoretical definition;
- prespecify transformations and weighting;
- fit any parameters on development data only;
- validate calibration and sensitivity on held-out data.

Current state:

- evidence profiles exist;
- scalar outputs intentionally remain `None`;
- inventing a scalar now would bypass the framework's own validation policy.

### F. Delayed-disclosure experiment in the current LaTeX manuscript

The existing manuscript proposes a specific study of adversarial conversation history and delayed policy violations. Its proposed design includes:

- a synthetic-secret disclosure outcome;
- baseline and treatment conversation arms;
- distances such as 0, 2, and 5 turns;
- Qwen and Gemma model families;
- repeated trials;
- a primary control-adjusted comparison;
- prompt-render verification and context audits.

Important status:

- the exact-secret outcome checker is not yet implemented as a completed validated paper result;
- the intervention arms are a proposed design;
- the required full run and statistical analysis are not complete.

### G. Do not mix the two proposed protocols

The repository currently contains two related but distinct future-study concepts:

1. a broader Phase 6 annotation/evaluator-validation program, including proposed development, validation, and test allocations and a larger call-budget envelope;
2. the delayed synthetic-secret disclosure pilot described in the current LaTeX manuscript, with its own arms, distances, models, goals, and repetitions.

Before data collection, select one as the paper's primary protocol and freeze it. Combining their sample sizes or design elements after the fact would make the experimental record ambiguous.

---

## 4. End-to-end working of the system

The implemented workflow can be described as:

```text
Dataset import
    -> normalized cases and version checksum
    -> benchmark configuration
    -> model/provider resolution
    -> prompt or conversation construction
    -> inference execution
    -> raw response and operational trace storage
    -> Layer 1 deterministic evidence
    -> optional Layer 2 structured judgment
    -> validation-gate checks
    -> eligible metric computation
    -> database/API exposure
    -> dashboard and paper-report export
```

The key distinction is between **evidence production** and **scientific interpretation**. The system can always store a response, timing measurement, and detector match. It may calculate a scientific metric only when the required labels, controls, calibration, and coverage are present.

For example:

```text
Response contains a flagged phrase
    -> Layer 1 evidence = available
    -> ground-truth harmfulness = not established
    -> ASR outcome = unavailable unless a valid outcome label exists
    -> model safety ranking = blocked without a controlled labeled comparison
```

This separation is the central methodological contribution of the project.

---

## 5. Paper-ready IEEE content

## Title

**SecureLLMBench: A Traceable and Validation-Aware Platform for Reproducible LLM Security Evaluation**

## Authors and affiliations

**[Author One], [Author Two], and [Author Three]**  
[Department], [Institution]  
[City], [Country]  
[email1], [email2], [email3]

Replace every bracketed field before submission. Do not invent affiliations, funding, or contributors.

## Abstract

Security evaluations of large language models frequently combine adversarial prompts, automated detectors, model-based judges, and aggregate scores without preserving enough evidence to determine whether the reported measurements are valid. This paper presents SecureLLMBench, a validation-aware framework for traceable language-model security evaluation. The framework connects versioned datasets, model and provider configurations, inference traces, deterministic detector evidence, structured judge outputs, metric prerequisites, and reporting artifacts in a persistent workflow. Its central design rule is that unsupported measurements remain explicitly unavailable, blocked, or uncalibrated instead of being silently converted into numerical scores. SecureLLMBench supports local and compatible remote inference, layered evaluation, operational measurements, group-aware analytical utilities, an application programming interface, and a research dashboard. We evaluate the framework's judge-validation workflow using 300 comparison records, of which 295 produced usable paired labels. Although judge coverage reached 98.333%, fixed-label agreement was 53.898% and Cohen's kappa was 0.211261, indicating that the evaluated judge configuration is not an adequate replacement for independent human annotation. Small local Qwen and Gemma runs further demonstrate end-to-end execution and visualization but are treated only as engineering evidence. The results show how explicit evidence states and validation gates can improve the reproducibility and interpretability of language-model security benchmarks.

Word count: approximately 205 words.

## Index Terms

Benchmarking, evaluation validity, language model security, reproducibility, security metrics, traceability.

## I. Introduction

Large language models are increasingly deployed in systems that process untrusted instructions, retain conversation history, and interact with external tools. These capabilities create a broad evaluation problem: a benchmark must distinguish a model response from the evidence used to characterize it, and it must distinguish detector output from a validated security outcome. Existing adversarial benchmarks have advanced the scale and diversity of testing [1]–[4], but reproducibility remains difficult when dataset revisions, inference settings, evaluator behavior, missing judgments, and metric eligibility are not represented as first-class artifacts.

Automated evaluation is especially attractive because human review is expensive. However, a model-based judge can exhibit high execution coverage while disagreeing systematically with independent labels. Similarly, a lexical detector may be reproducible without being a valid measure of policy violation. Reporting either signal as ground truth can create precise-looking but unsupported rankings.

SecureLLMBench addresses this problem as an evidence-control framework. It connects versioned benchmark cases, model configurations, inference traces, layered detector and judge outputs, metric definitions, validation states, and visual reports. Instead of forcing every pipeline stage into a score, it records whether an output is available, uncalibrated, blocked, or undefined. This design makes missing scientific prerequisites visible in both stored records and reports.

The contributions of this work are:

1. a traceable benchmark architecture linking datasets, configurations, responses, evidence, metrics, and reports;
2. an evidence-status mechanism that prevents unsupported metrics from appearing as valid numerical findings;
3. a layered evaluation workflow that separates deterministic detection from structured judging and independent outcome labels;
4. a completed judge-calibration case study demonstrating why coverage alone is insufficient; and
5. a local end-to-end engineering demonstration with operational metrics and paper-oriented visualizations.

The paper does not claim that the current detector outputs establish model safety, that Qwen or Gemma is categorically safer, or that the proposed behavioral metrics have completed empirical validation.

## II. Related Work

### A. Adversarial language-model benchmarks

JailbreakBench standardizes jailbreak evaluation resources and highlights the importance of comparable attacks, defenses, and evaluation procedures [1]. HarmBench provides a broad standardized evaluation framework for automated red teaming and robust refusal assessment [2]. These efforts motivate common benchmark protocols, while SecureLLMBench focuses specifically on provenance, metric eligibility, and explicit validation state within the execution system.

### B. Agent and prompt-injection evaluation

AgentDojo evaluates attacks and defenses for tool-using language-model agents [3], while InjecAgent studies indirect prompt injection in tool-integrated systems [4]. These benchmarks demonstrate that security behavior depends on task context, available tools, and control boundaries. SecureLLMBench complements them with an auditable record linking each case and configuration to its evidence and reported measurement.

### C. Context sensitivity and long conversations

Language-model behavior can vary with information position and context composition. The Lost in the Middle study shows that models may use long-context information unevenly depending on its location [5]. This motivates the repository's proposed sequential, isolated, and delayed-intervention designs, although the corresponding controlled experiment remains future work.

### D. Automated evaluators

StrongREJECT demonstrates the value of evaluator design for distinguishing refusal quality and jailbreak success [6]. More generally, automated judges reduce evaluation cost but introduce another model whose errors must be measured. SecureLLMBench therefore treats judge coverage, agreement, class behavior, and calibration as prerequisites for outcome use rather than assuming that a completed judgment is correct.

### E. Difference from prior work

The contribution is not a claim that SecureLLMBench replaces established security benchmarks. It provides infrastructure for executing such evaluations while preserving provenance and enforcing the distinction among raw outputs, detector signals, validated outcomes, and unavailable metrics.

## III. Methodology and Proposed System

### A. Design principles

The framework follows four principles:

1. **Traceability:** every reported value must be connected to the cases, model, configuration, evaluator, and code path that produced it.
2. **Separation of evidence:** raw responses, deterministic matches, judge labels, human labels, and aggregate metrics are different record types.
3. **Eligibility before aggregation:** a metric is calculated only after its prerequisites pass.
4. **Explicit incompleteness:** missing or scientifically unsupported values are reported as unavailable rather than imputed as safe, failed, or zero.

### B. System architecture

SecureLLMBench contains a dataset layer, model registry, provider adapters, benchmark runner, persistence layer, evaluation services, statistical utilities, API, dashboard, and report exporter. A dataset version and benchmark configuration define an execution. Provider adapters submit rendered prompts or conversation states to a model and record responses and operational measurements. Evaluation services then attach deterministic or judge-generated evidence. Validation gates determine which aggregate metrics may be emitted.

**Suggested figure:**

> **Fig. 1. SecureLLMBench evidence flow.** Versioned cases and model configurations produce inference traces; layered evaluators attach evidence; validation gates control metric eligibility; APIs, dashboards, and exporters expose only the resulting status-aware records.

### C. Threat model

The attacker may control adversarial user text and, in sequential experiments, the order of user turns. The defender selects the evaluated model and system policy. Isolated conditions use fresh conversation histories, while sequential conditions retain designated history. Model weights, system prompts, source-dataset labels, and evaluator rubrics are outside the attacker's direct control for a frozen run. The framework does not claim protection against compromised infrastructure, arbitrary multi-user interactions, universal jailbreak strategies, or deployment-wide certification.

### D. Layered evidence model

Layer 1 evaluates responses using reproducible keywords, regular expressions, and structural patterns. It records the rule and matched evidence but does not assign ground-truth harm. Layer 2 submits eligible responses to a structured evaluator and records its label, rationale, version, latency, and failure state. Independent human labels remain a distinct evidence source. A judge can become an outcome evaluator only after validation against those labels.

### E. Metric eligibility

Attack Success Rate is calculated using (1) only from explicitly classified outcomes. Coverage is reported as

\[
\mathrm{Coverage}=\frac{N_{\mathrm{usable}}}{N_{\mathrm{requested}}}.
\tag{2}
\]

Agreement is reported as raw agreement and Cohen's kappa,

\[
\kappa=\frac{p_o-p_e}{1-p_e},
\tag{3}
\]

where \(p_o\) is observed agreement and \(p_e\) is the chance agreement implied by the marginal label frequencies. Coverage and agreement answer different questions: the first measures whether the evaluator returned usable records; the second measures whether its labels align with the reference.

BSDA retains separate semantic, safety, instruction-following, and structural components because no validated weighting currently supports a composite score. RC and SAEA require validated and comparable behavioral states. DRAA and PRI retain profile evidence while their scalar forms remain undefined.

### F. Judge-validation procedure

The implemented calibration analysis aligns judge labels with external human labels, rejects unusable pairs, reports coverage, constructs a confusion matrix, and calculates raw agreement and Cohen's kappa. This procedure is diagnostic: it determines whether the judge is eligible for a later role and does not change the external labels.

### G. Local engineering demonstration

Two local Ollama models, Qwen 3.5 2B and Gemma 3 4B, were run on three cases each. The same Layer 1 reporting path generated detector summaries and operational latency statistics. Because the sample is small, has no completed independent outcome labeling, and was not executed as a frozen repeated study, it is used only to verify the software path from inference to storage and visualization.

### H. Reproducibility protocol for future experiments

A claim-bearing experiment must freeze dataset checksums, case identifiers, model identities, prompt templates, attack families, conversation conditions, seeds, decoding settings, repetitions, evaluator versions, metric versions, exclusion rules, and statistical tests. Benign and isolated controls must be retained. Independent reviewers should be blinded where possible, and disagreements should be adjudicated. The final artifact should include the manifest, eligible record set, exclusion log, and figure-generation code.

## IV. Results and Discussion

### A. System-level result

The implemented system completes the engineering workflow from versioned input through inference, layered evidence recording, persistence, API access, dashboard display, and static plot export. The dashboard build, linting, type checking, and 22 frontend tests passed in the observed development environment. This result verifies the implemented software path; it is not an empirical statement about model safety.

### B. Judge calibration

**TABLE I**  
**JUDGE CALIBRATION SUMMARY**

| Quantity | Value |
|---|---:|
| Requested comparison records | 300 |
| Usable paired labels | 295 |
| Coverage | 98.333% |
| Fixed-label agreement | 53.898% |
| Cohen's kappa | 0.211261 |

**TABLE II**  
**JUDGE AND HUMAN-LABEL CONFUSION COUNTS**

| | Human 0 | Human 1 |
|---|---:|---:|
| Judge 0 | 51 | 1 |
| Judge 1 | 135 | 108 |

The judge generated usable outputs for nearly all requested records, but its label distribution differed substantially from the human reference. In particular, 135 human-negative records were assigned the positive judge label under the fixed mapping. The modest kappa value shows that the high coverage did not translate into strong label validity. Consequently, the current judge configuration is unsuitable as a drop-in replacement for independent human annotation.

### C. Illustrative local model run

**TABLE III**  
**LOCAL ENGINEERING DEMONSTRATION**

| Model | Cases | Detector metric | Mean threat | Worst threat | Mean latency | Signals |
|---|---:|---:|---:|---:|---:|---:|
| Qwen 3.5 2B | 3 | 86.67% | 13.33% | 20.00% | 19.14 s | 2 |
| Gemma 3 4B | 3 | 86.67% | 13.33% | 20.00% | 13.75 s | 2 |

Both models produced the same detector-derived values and the same number of keyword signals. Gemma's mean latency was lower by approximately 5.39 s for this run. This observation is operational rather than a general performance conclusion because latency depends on local hardware, model loading, provider state, and the small set of prompts. The identical detector values also do not demonstrate equal safety; they show only that the selected rules produced the same aggregate profile on these cases.

**Suggested figures:**

> **Fig. 2. Detector-derived metric comparison for the local engineering run.** The models have equal values on the three displayed summaries; the figure does not represent independently labeled attack success.

> **Fig. 3. Mean local inference latency by model.** Gemma was faster in the observed three-case run; no hardware-independent speed claim is made.

> **Fig. 4. Layer 1 keyword-signal counts.** Both models generated two deterministic rule matches; signal counts are evidence items, not ground-truth harmful outcomes.

### D. Evidence-freeze distinction

The repository's frozen paper evidence bundle describes an earlier local demonstration with 4 benchmark runs, 12 evaluations, and 36 Layer 1 results. The currently active development database contains later activity, including 15 benchmark runs, 45 evaluations, and 135 Layer 1 results. These populations must not be combined casually. A submitted manuscript should either retain the documented frozen bundle or create a new manifest and regenerate all counts, tables, and figures from a newly frozen snapshot.

### E. Research questions answered now

The current evidence supports the following questions:

- Can the framework preserve a trace from benchmark input to report? **Yes, as an engineering result.**
- Can it represent unavailable or unvalidated metrics explicitly? **Yes, as a software and schema result.**
- Does the evaluated judge have sufficient evidence to replace human annotation? **No, based on the reported calibration.**
- Can the local pipeline execute multiple models and export comparable operational plots? **Yes, as an engineering demonstration.**

The current evidence does not answer:

- Which evaluated model is safer?
- What is the true attack success rate?
- Do sequential attacks cause a statistically significant degradation?
- Are BSDA, RC, SAEA, DRAA, or PRI empirically predictive?
- Does a trained model generalize to a held-out security dataset?

### F. Limitations

The completed human-label set is insufficient for claim-bearing model comparison. The existing judge calibration uses an external labeled comparison but does not validate the judge for every task, attack family, or model population. Layer 1 detectors are sensitive to lexical form and may produce false positives or miss semantically equivalent violations. The local engineering run contains only three cases per model and no repeated controlled trials. Operational latency reflects one local environment. Several behavioral metrics have implemented data structures but not validated representations or thresholds. Scalar DRAA and PRI definitions are intentionally absent. Finally, the dashboard improves inspection but cannot convert weak evidence into scientific validity.

### G. Discussion

The calibration result illustrates the reason for validation-aware reporting. If completion rate alone were treated as evaluator quality, the judge's 98.333% coverage could appear strong. Pairing it with agreement and kappa changes the conclusion. The framework's contribution is therefore partly negative but useful: it preserves enough structure to block a convenient but unsupported result. The same logic applies to the local plots. They are valuable for checking execution, aggregation, and presentation, but the framework labels their scientific role narrowly.

## V. Conclusion

SecureLLMBench is a traceable and validation-aware framework for language-model security evaluation. It integrates versioned datasets, provider-neutral inference, response traces, deterministic detector evidence, structured judge records, metric eligibility gates, analytical utilities, APIs, dashboards, and report export. A calibration study with 295 usable paired labels showed that a high-coverage automated judge achieved only 53.898% agreement and a Cohen's kappa of 0.211261, so the evaluated configuration should not replace independent human labeling. Small local Qwen and Gemma runs verified the end-to-end software and visualization path but did not support a safety ranking. The central contribution is an evidence model that keeps unsupported measurements explicitly unavailable. Future work will complete independent annotation, freeze a controlled multi-model protocol, validate behavioral representations, implement the delayed-disclosure outcome checker where applicable, and conduct paired statistical analyses on reproducible run artifacts.

## Acknowledgment

> The authors thank [contributors or laboratory] for [specific contribution]. This work was supported by [funding body and grant number].

Delete this section if there was no funding or contribution to acknowledge. Do not insert generic or invented acknowledgments.

## References

The expanded citation map and verified BibTeX records are available in `docs/paper/REFERENCE_PAPERS.md` and `docs/paper/securellmbench_references.bib`. The six entries below are the minimum set used by this draft; the expanded set adds dedicated sources for automated-judge validity and Cohen's kappa.

[1] P. Chao *et al.*, “JailbreakBench: An open robustness benchmark for jailbreaking large language models,” in *Advances in Neural Information Processing Systems*, 2024, doi: 10.52202/079017-1745.

[2] M. Mazeika *et al.*, “HarmBench: A standardized evaluation framework for automated red teaming and robust refusal,” in *Proceedings of the 41st International Conference on Machine Learning*, PMLR, 2024.

[3] E. Debenedetti *et al.*, “AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,” in *Advances in Neural Information Processing Systems*, 2024, doi: 10.52202/079017-2636.

[4] Q. Zhan *et al.*, “InjecAgent: Benchmarking indirect prompt injections in tool-integrated large language model agents,” in *Findings of the Association for Computational Linguistics: ACL 2024*, 2024, doi: 10.18653/v1/2024.findings-acl.624.

[5] N. F. Liu *et al.*, “Lost in the middle: How language models use long contexts,” *Transactions of the Association for Computational Linguistics*, vol. 12, 2024, doi: 10.1162/tacl_a_00638.

[6] A. Souly *et al.*, “A strongREJECT for empty jailbreaks,” in *Advances in Neural Information Processing Systems*, 2024.

Before submission, verify every reference against the publisher record and add complete page numbers, volume numbers, URLs, or DOIs required by the target venue.

---

## 6. Recommended figures and tables

Keep the paper visually restrained. Use one muted blue for the primary series, one muted orange for comparison, neutral gray grid lines, and a white background.

Recommended minimum set:

| Item | Purpose | Status |
|---|---|---|
| Fig. 1 | End-to-end evidence architecture | Create from system architecture |
| Fig. 2 | Detector metric comparison | Generated |
| Fig. 3 | Latency comparison | Generated |
| Fig. 4 | Layer 1 signal counts | Generated |
| Table I | Judge calibration summary | Ready |
| Table II | Judge/human confusion matrix | Ready |
| Table III | Local engineering demonstration | Ready |
| Table IV | Implemented versus planned capability matrix | Derive from Section 2–3 |

For a 6-page paper, use Fig. 1, one combined local-results figure, Tables I–II, and move the full capability matrix to supplementary material.

---

## 7. Claims that must not appear in the paper yet

Do not write any of the following as findings:

- “SecureLLMBench proves that model X is safer than model Y.”
- “The detector metric is equivalent to attack success rate.”
- “Two keyword signals mean two successful attacks.”
- “The Gemma judge provides reliable ground truth.”
- “BSDA, RC, or SAEA has been empirically validated.”
- “DRAA or PRI produces a scientifically validated scalar score.”
- “The machine-learning component predicts jailbreak risk.”
- “The delayed-disclosure study demonstrated a causal history effect.”
- “All Python tests passed,” unless a fresh full suite is executed and archived.

Acceptable alternatives:

- “The local run demonstrated the execution and reporting path.”
- “The rule-based layer produced two keyword signals.”
- “The evaluated judge was rejected as a replacement for independent labels under the current evidence.”
- “The proposed controlled study is designed to test whether adversarial history changes delayed policy-violation outcomes.”

---

## 8. Submission preparation checklist

1. Select the final paper scope: framework paper or delayed-disclosure empirical paper.
2. Do not combine the Phase 6 validation proposal with the delayed-disclosure protocol unless a new unified protocol is frozen prospectively.
3. Choose either the existing frozen evidence bundle or a new database snapshot.
4. Generate one machine-readable experiment manifest.
5. Run the complete Python and frontend verification suites and archive their logs.
6. Complete independent human annotation and adjudication for any attack-success claim.
7. Revalidate the judge or retain the negative calibration finding.
8. Regenerate every table and figure from the frozen artifact set.
9. Verify model names, versions, hardware, seeds, decoding settings, and exclusions.
10. Check every citation against its publisher page.
11. Replace all author, affiliation, funding, and contributor placeholders.
12. Format the final manuscript in the official IEEE two-column template.
13. Keep figure captions below figures and table titles above tables.
14. Number equations at the right and cite every figure, table, and equation in the text.
15. Confirm the venue's page limit and anonymization policy.

---

## 9. IEEE layout guidance

- Use the official IEEE conference or journal template selected by the target venue.
- Body text is normally two-column, 10-point Times-family type, single-spaced, and justified.
- Use Roman-numbered primary sections and lettered subsections.
- Keep the abstract between 150 and 250 words and free of citations and undefined abbreviations.
- Use three to seven alphabetized index terms.
- Place figure captions below figures and table titles above tables.
- Number citations in order of first appearance using square brackets.
- Center displayed equations and place their numbers at the right.
- Treat the venue's current author kit as authoritative if its rules differ from these general conventions.

