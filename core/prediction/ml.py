"""Future ML prediction contract."""
from collections.abc import Sequence
from typing import Protocol
class Predictor(Protocol):
    def predict(self, features: Sequence[float]) -> float: ...
