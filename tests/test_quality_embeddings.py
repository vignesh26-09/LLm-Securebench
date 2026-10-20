import pytest

from core.dataset.models import Dataset, DatasetRecord
from core.dataset.quality import calculate_dqi, estimate_novelty


@pytest.mark.parametrize("embeddings", [(), (None, None), ((1.0, 0.0),), (None, (1.0, 0.0))])
def test_fewer_than_two_usable_embeddings_are_unavailable(embeddings):
    dataset = Dataset(tuple(
        DatasetRecord(id=str(index), prompt=f"synthetic {index}")
        for index in range(len(embeddings))
    ))
    result = calculate_dqi(dataset, embeddings=embeddings)

    assert result.components["novelty"] is None
    assert estimate_novelty(embeddings) is None
    assert result.score is None
    assert result.status == "unavailable"
    assert result.reason == "semantic_embeddings_unavailable"


@pytest.mark.parametrize("embeddings, novelty", [
    (((1.0, 0.0), (0.0, 1.0)), 0.5),
    (((1.0, 0.0), (1.0, 0.0), (0.0, 1.0), None), 1 / 6),
])
def test_two_or_more_usable_embeddings_preserve_novelty(embeddings, novelty):
    dataset = Dataset(tuple(
        DatasetRecord(id=str(index), prompt=f"synthetic {index}")
        for index in range(len(embeddings))
    ))
    result = calculate_dqi(dataset, embeddings=embeddings)

    assert estimate_novelty(embeddings) == pytest.approx(novelty)
    assert result.components["novelty"] == pytest.approx(novelty)
    assert result.status == "computed"
    assert result.reason is None
    assert result.score is not None
