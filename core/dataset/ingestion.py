"""Dataset loader ports and dispatching helpers."""

from pathlib import Path
from typing import Protocol

from core.dataset.models import Dataset


class DatasetLoader(Protocol):
    """Loads a dataset from an external representation."""

    def load(self, path: Path) -> Dataset: ...


def loader_for_path(path: Path) -> DatasetLoader:
    """Select a built-in loader by file suffix without exposing it to callers."""
    from core.dataset.loaders import CsvDatasetLoader, JsonDatasetLoader, JsonlDatasetLoader

    loaders = {
        ".json": JsonDatasetLoader(),
        ".jsonl": JsonlDatasetLoader(),
        ".csv": CsvDatasetLoader(),
    }
    try:
        return loaders[path.suffix.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported dataset format: {path.suffix or '<none>'}") from error
