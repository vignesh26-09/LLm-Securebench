"""Optional CPU-compatible semantic embedding, similarity, and clustering adapters."""

import math
from dataclasses import dataclass
from typing import Protocol, Sequence

from core.dataset.models import Dataset

Embedding = tuple[float, ...]


class EmbeddingProvider(Protocol):
    """External semantic embedding port; adapters may use local CPU models."""

    @property
    def model_name(self) -> str: ...

    def embed(self, texts: Sequence[str], *, batch_size: int = 32) -> tuple[Embedding, ...]: ...


class SentenceTransformerEmbeddingProvider:
    """Lazy SentenceTransformers adapter. Requires the optional `semantic` extra."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", *, device: str = "cpu") -> None:
        self._model_name = model_name
        self._device = device
        self._model: object | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, texts: Sequence[str], *, batch_size: int = 32) -> tuple[Embedding, ...]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if not texts:
            return ()
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as error:
                raise RuntimeError("Install semantic dependencies: pip install -e '.[semantic]'") from error
            self._model = SentenceTransformer(self._model_name, device=self._device)
        vectors = self._model.encode(list(texts), batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
        return tuple(tuple(float(value) for value in vector) for vector in vectors)


def embed_dataset_prompts(dataset: Dataset, provider: EmbeddingProvider, *, batch_size: int = 32) -> tuple[Embedding | None, ...]:
    """Embed available prompts in batches while retaining dataset record positions."""
    positions = [index for index, record in enumerate(dataset.records) if record.prompt]
    vectors = provider.embed([dataset.records[index].prompt or "" for index in positions], batch_size=batch_size)
    if len(vectors) != len(positions):
        raise ValueError("embedding provider returned an unexpected number of vectors")
    results: list[Embedding | None] = [None] * len(dataset.records)
    for index, vector in zip(positions, vectors, strict=True):
        results[index] = vector
    return tuple(results)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity with explicit dimension and zero-vector handling."""
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    if not left:
        raise ValueError("vectors must not be empty")
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return numerator / denominator if denominator else 0.0


@dataclass(frozen=True, slots=True)
class NearDuplicatePair:
    first_index: int
    second_index: int
    similarity: float


def find_near_duplicates(embeddings: Sequence[Embedding | None], *, threshold: float = 0.9) -> tuple[NearDuplicatePair, ...]:
    """Find record pairs whose cosine similarity meets a chosen threshold."""
    if not -1.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between -1 and 1")
    pairs: list[NearDuplicatePair] = []
    for first, vector in enumerate(embeddings):
        if vector is None:
            continue
        for second in range(first + 1, len(embeddings)):
            other = embeddings[second]
            if other is not None:
                similarity = cosine_similarity(vector, other)
                if similarity >= threshold:
                    pairs.append(NearDuplicatePair(first, second, similarity))
    return tuple(pairs)


def cluster_dbscan(embeddings: Sequence[Embedding], *, eps: float = 0.2, min_samples: int = 2) -> tuple[int, ...]:
    """Cluster embeddings using optional scikit-learn DBSCAN with cosine distance."""
    try:
        from sklearn.cluster import DBSCAN
    except ImportError as error:
        raise RuntimeError("Install semantic dependencies: pip install -e '.[semantic]'") from error
    if not embeddings:
        return ()
    return tuple(int(label) for label in DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit_predict(embeddings))


def cluster_hdbscan(embeddings: Sequence[Embedding], *, min_cluster_size: int = 2) -> tuple[int, ...]:
    """Cluster embeddings using optional HDBSCAN, if explicitly installed."""
    try:
        import hdbscan
    except ImportError as error:
        raise RuntimeError("Install HDBSCAN: pip install -e '.[semantic,hdbscan]'") from error
    if not embeddings:
        return ()
    return tuple(int(label) for label in hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean").fit_predict(embeddings))
