# Dataset semantic analysis and DQI

Semantic analysis is separated behind `EmbeddingProvider`. The default adapter
uses SentenceTransformers on `cpu`; callers can inject any compatible provider.
Embeddings are never required for parsing, normalization, exact duplicates, or
the command-line processing workflow.

`calculate_dqi` combines six independently exposed components with configurable,
non-negative weights: exact-duplicate quality, prompt coverage, category entropy,
embedding novelty, difficulty entropy, and category balance. Its score is the
weighted mean of component scores. Novelty maps cosine similarity into `[0, 1]`
using `(1 - maximum_similarity) / 2` per record.

DQI is exploratory and must not be represented as scientifically validated until
it has been evaluated against a published methodology and relevant datasets.
