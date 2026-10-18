"""Layer 2 semantic judging public boundaries."""

from core.judging.models import JudgeResult
from core.judging.provider import JudgeProvider

SemanticJudge = JudgeProvider
SemanticJudgment = JudgeResult

__all__ = ["JudgeProvider", "JudgeResult", "SemanticJudge", "SemanticJudgment"]
