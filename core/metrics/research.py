"""Research metric contracts."""
from collections.abc import Iterable
from typing import Protocol
class ResearchMetric(Protocol):
    name: str
    def calculate(self, values: Iterable[float]) -> float: ...
