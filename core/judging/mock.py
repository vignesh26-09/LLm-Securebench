"""Deterministic mock judge provider for CPU-only tests; no model or network is used."""

from collections import deque
from typing import Iterable

from core.judging.provider import JudgeProviderRequest, JudgeProviderResponse, JudgeTimeoutError


class MockJudgeProvider:
    provider_name = "mock-judge"

    def __init__(self, outputs: Iterable[str | Exception]) -> None:
        self._outputs = deque(outputs)
        self.requests: list[JudgeProviderRequest] = []

    def judge(self, request: JudgeProviderRequest) -> JudgeProviderResponse:
        self.requests.append(request)
        if not self._outputs:
            raise RuntimeError("Mock judge has no configured output")
        output = self._outputs.popleft()
        if isinstance(output, Exception):
            raise output
        return JudgeProviderResponse(output, {"deterministic": True, "temperature": request.config.temperature})


def timeout_error(message: str = "mock judge timeout") -> JudgeTimeoutError:
    """Convenience constructor for deterministic timeout tests."""
    return JudgeTimeoutError(message)
