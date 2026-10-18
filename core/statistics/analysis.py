"""Statistical analysis contracts."""
from collections.abc import Iterable
from typing import Protocol
class StatisticalAnalyzer(Protocol):
    def summarize(self, values: Iterable[float]) -> dict[str, float]: ...
