# SecureLLMBench research plan

## Motivation

Security benchmark outcomes depend on both model behavior and the quality,
coverage, provenance, and duplication characteristics of their datasets.
SecureLLMBench is intended to provide modular tooling for examining those inputs
before broader model-security benchmark workflows are introduced.

## Core hypothesis

A transparent, modular dataset-processing layer can make security-benchmark
datasets easier to inspect, compare, and reproduce. This is a research direction,
not a demonstrated scientific result.

## Research questions

- How do duplication, field coverage, category composition, difficulty labels,
  and semantic similarity affect benchmark interpretation?
- Which dataset-quality signals are reliable across independently annotated and
  independently sourced security datasets?
- What ground truth and validation design are necessary before a composite
  dataset-quality metric can support scientific claims?
- How should dataset diagnostics connect to future detection, judging, model,
  and benchmark-execution components without confounding their results?

## Phase 0 research direction

Phase 0 establishes the conceptual direction: a cleanly separated benchmark
architecture with explicit dataset ingestion and processing boundaries, followed
by research-grade evaluation only after datasets, labels, and validation plans are
defined. It does not establish a validated metric, a model-security result, or an
LLM evaluation protocol.

## Current engineering progression

The repository currently reflects these engineering stages:

1. **Phase 1 — foundation:** modular package skeleton, clean-architecture
   boundaries, health check, configuration/data/docs/test layout.
2. **Phase 2 — dataset foundation:** explicit dataset schemas, loaders,
   validation, normalization, exact duplicate analysis, metadata, splitting, and
   descriptive statistics.
3. **Phase 3 — semantic dataset analysis:** optional embedding-provider boundary,
   CPU-oriented SentenceTransformer adapter, cosine similarity, near duplicates,
   optional clustering adapters, descriptive semantic analysis, and exploratory
   DQI implementation.

These phases are implementation progress, not validated research phases.

## Proposed experimental progression

1. Define a dataset inventory and provenance requirements for candidate security
   datasets.
2. Establish annotation guidance and ground truth for duplicates, categories,
   difficulty, attack types, and relevant semantic relationships.
3. Evaluate individual diagnostics against that ground truth, including
   sensitivity to normalization, embedding model choice, thresholds, and sampling.
4. Predefine benchmark splits and analyses to limit leakage and post-hoc metric
   selection.
5. Compare datasets and metrics across multiple sources and independently held-out
   evaluation material.
6. Only after empirical evaluation, assess whether any composite metric supports
   a defensible scientific claim.

## Ground-truth requirements

Future validation requires documented provenance, stable dataset versions,
annotation definitions, inter-annotator agreement or equivalent adjudication,
and held-out reference material. Embedding-based near duplicates and novelty need
human-reviewed reference labels; dataset fields alone are not ground truth.

## Validation requirements

Scientific contribution requires reproducible protocols, clear baselines,
ablation of individual components, threshold/model sensitivity analysis,
uncertainty reporting, and independent or held-out validation. A deterministic
implementation and passing software tests verify engineering behavior only.

## Engineering versus scientific validation

The repository **implements** dataset processing and an exploratory DQI formula.
It does **not** validate that DQI measures dataset quality, predicts benchmark
quality, or generalizes across datasets. It also does not implement or validate
benchmark algorithms, LLM inference, detection/judging systems, ML prediction,
or future named metrics.

## Open research questions

- Which source datasets and threat taxonomies are in scope?
- What operational definition of difficulty is appropriate and who labels it?
- How should semantic similarity thresholds be calibrated across languages and
  embedding models?
- What target outcome, if any, should a future dataset-quality metric predict?
- How will class imbalance, annotation noise, provenance, and temporal changes be
  represented?
- Whether proposed future metrics such as BSDA, SAEA, DRAA, or PRI have precise
  definitions and empirical validation plans. They are not implemented here.
