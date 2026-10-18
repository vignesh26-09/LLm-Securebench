"""Composable, deterministic processing for already-loaded datasets."""

from typing import Protocol

from core.dataset.models import Dataset


class DatasetProcessor(Protocol):
    """Transforms a dataset without depending on its source format."""

    def process(self, dataset: Dataset) -> Dataset: ...
