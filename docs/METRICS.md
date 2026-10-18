# Metrics status

## Status terminology

- **Implemented:** code exists in the repository and is covered where
  deterministic by unit tests.
- **Exploratory:** implemented for investigation, but not scientifically
  validated as a research metric.
- **Planned:** no implementation claim is made.

## Implemented dataset-quality components

| Component | Status | Current interpretation |
| --- | --- | --- |
| Exact duplicate grouping | Implemented | Groups equal normalized prompts using SHA-256. |
| Near-duplicate pairs | Implemented with embeddings | Returns pairs at or above a caller-set cosine threshold. |
| Coverage statistics | Implemented | Presence rates for record fields; DQI uses prompt coverage. |
| Difficulty distribution | Implemented | Counts supplied difficulty labels. |
| Category balance | Implemented | Category counts and normalized categorical entropy. |
| Novelty estimate | Exploratory | Mean local distance from the most similar embedded record. |
| DQI | Exploratory | Configurable weighted composite described below. |

## Current DQI formula

`calculate_dqi` computes a weighted mean over these components, each with default
weight `1.0` and required non-negative weights:

| DQI component | Current value |
| --- | --- |
| `duplicate_quality` | `1 - redundant_exact_duplicate_records / record_count` (or `0` for an empty dataset). |
| `coverage` | Prompt presence rate. |
| `entropy` | Normalized entropy of present category labels. |
| `novelty` | Mean `(1 - maximum cosine similarity) / 2` over supplied embeddings; `0` if embeddings are not supplied. |
| `difficulty` | Normalized entropy of present difficulty labels. |
| `balance` | Normalized entropy of present category labels. |

DQI is **EXPLORATORY and NOT SCIENTIFICALLY VALIDATED**. Its components contain
design choices that require independent empirical validation, calibration, and
ablation before they can be used for scientific claims. The current `entropy` and
`balance` components intentionally both use category entropy; this documents the
existing implementation and does not imply that the design is validated.

## Planned metrics and research work

BSDA, SAEA, DRAA, PRI, model-security outcomes, ML prediction metrics, and any
other future research metrics are **PLANNED only**. This repository contains no
implementation or validation of them. Definitions, ground truth, baselines,
evaluation protocols, and validation criteria must be agreed before introducing
such metrics.

## Non-metric utilities

Cosine similarity, embedding generation, DBSCAN, and HDBSCAN adapters are
analysis utilities. Their presence does not validate any interpretation, threshold,
or clustering result.
