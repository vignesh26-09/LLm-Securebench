"""Extension point for future approved semantic-drift calculations."""

from typing import Protocol

from core.judging.models import JudgeCase


class SemanticDriftCalculator(Protocol):
    """Reserved until an approved, validated semantic-drift calculation is available."""
    def calculate(self, case: JudgeCase) -> object: ...
