# Dataset subsystem specification

## Scope and status

This document describes the current implemented dataset subsystem. It includes
optional semantic adapters and an **EXPLORATORY, NOT SCIENTIFICALLY VALIDATED**
Dataset Quality Index (DQI). It does not implement embeddings by default, LLM
inference, clustering by default, or broader research algorithms.

## Core schemas

`DatasetRecord` fields are all optional except that validation requires at least
one non-empty `id` or `prompt`:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | `str | None` | Source or logical record identifier. |
| `prompt` | `str | None` | Text submitted for analysis. |
| `category` | `str | None` | Dataset-defined category. |
| `attack_type` | `str | None` | Dataset-defined attack type. |
| `source` | `str | None` | Record-level source label. |
| `language` | `str | None` | Record language label. |
| `difficulty` | `str | None` | Dataset-defined difficulty label. |
| `metadata` | mapping | Source-specific structured values. |

`Dataset` contains an immutable tuple of records and `DatasetMetadata`.
Dataset-level metadata supports `name`, `description`, `source`, and a
`DatasetVersion` with `version`, `released_at`, and `checksum`. Additional
dataset-level keys are retained in metadata `extra`.

## Input formats

- **JSON:** a top-level record array, or an object with a `records` array and an
  optional `metadata` object.
- **JSONL:** one JSON record object per nonblank line. Dataset-level metadata is
  not represented by the current JSONL loader.
- **CSV:** header row using record field names. Empty values are omitted; the
  optional `metadata` cell must contain a JSON object.

The `DatasetLoader` protocol and `loader_for_path` dispatch allow an external
loader to be added without changing the processing pipeline.

## Validation rules

- Every record must be an object/mapping.
- Only the documented record fields are accepted; unknown record fields fail
  validation rather than silently changing the schema.
- Text fields must be strings or `null`.
- `metadata` must be an object; `null` becomes an empty mapping.
- A record requires an `id` or a `prompt`.
- JSON requires a record list or an object containing a `records` list; CSV
  requires a header; invalid JSON/JSONL and invalid CSV metadata fail loading.

## Normalization and exact duplicates

`normalize_text` uses Unicode NFC, converts CRLF/CR line endings to LF, collapses
horizontal whitespace within each line, trims each line, and trims outer text.
`TextNormalizer` applies this to all optional text fields while retaining metadata.

Exact duplicate analysis hashes nonempty normalized prompts with SHA-256 and
returns groups with matching fingerprints. It is exact normalized-text matching,
not semantic duplicate detection.

## Splitting and descriptive statistics

`split_train_evaluation` uses a seed and SHA-256 bucket derived from `id`, prompt,
or record index. This creates a deterministic train/evaluation assignment for a
given dataset, seed, and evaluation fraction.

`calculate_dataset_statistics` reports record and prompt counts, missing-field
counts, and category, attack-type, and language distributions.

## Semantic analysis

`EmbeddingProvider` is a source-independent interface. The optional
`SentenceTransformerEmbeddingProvider` defaults to `all-MiniLM-L6-v2` and
`device="cpu"`; it is lazy-loaded and requires the optional `semantic` dependency
extra. `embed_dataset_prompts` batches nonempty prompts while preserving record
positions. Cosine similarity and near-duplicate pair detection are implemented
without a mandatory third-party runtime dependency.

DBSCAN is available only with the optional `semantic` extra; HDBSCAN is available
only with the optional `hdbscan` extra. Neither is part of the dependency-free
CLI workflow.

## Exploratory DQI

DQI is **EXPLORATORY and NOT SCIENTIFICALLY VALIDATED**. The current formula is a
weighted mean of six configurable non-negative components:

1. duplicate quality: one minus redundant exact-duplicate records divided by all
   records;
2. coverage: prompt presence rate;
3. entropy: normalized category entropy;
4. novelty: mean local `(1 - maximum cosine similarity) / 2` when embeddings are
   supplied, otherwise `0`;
5. difficulty: normalized difficulty-label entropy;
6. balance: normalized category entropy.

Default weights are 1.0. This formula is an implementation detail for exploratory
research use and must not be interpreted as a validated measure of dataset
quality.

## Future research dataset requirements

Future experiments need documented licensing/provenance, versioning/checksums,
clear threat taxonomy and label definitions, multilingual handling where relevant,
difficulty annotation guidance, duplicate/near-duplicate review labels, and
predefined train/evaluation splits. They also need independent or held-out ground
truth before semantic diagnostics or DQI can support research conclusions.
