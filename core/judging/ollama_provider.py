"""Ollama-backed local Layer 2 judge provider; uses installed models only."""

from __future__ import annotations

import json
import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.inference.ollama_provider import ENDPOINT, installed_models, ollama_timeout, request_json
from core.judging.provider import JudgeProviderError, JudgeProviderRequest, JudgeProviderResponse, JudgeTimeoutError


class OllamaJudgeProvider:
    provider_name = "ollama-local-judge"

    def __init__(self, *, endpoint: str = ENDPOINT) -> None:
        self.endpoint = endpoint.rstrip("/")

    def assert_model_installed(self, model_name: str) -> str | None:
        for model in installed_models():
            if model.get("name") == model_name:
                return model.get("digest")
        raise JudgeProviderError("Configured Ollama judge model is not installed; automatic downloads are disabled")

    def judge(self, request: JudgeProviderRequest) -> JudgeProviderResponse:
        digest = self.assert_model_installed(request.config.model)
        body = {
            "model": request.config.model,
            "prompt": request.prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": request.config.temperature,
                "seed": request.config.seed,
                "num_predict": 384,
            },
            "keep_alive": "5m",
        }
        started = perf_counter()
        try:
            value = request_json(Request(f"{self.endpoint}/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), request.config.timeout_seconds or ollama_timeout(), opener=urlopen)
            if value.get("done") is not True or not isinstance(value.get("response"), str):
                raise JudgeProviderError("Ollama judge returned an incomplete or invalid response")
        except (TimeoutError, socket.timeout) as error:
            raise JudgeTimeoutError("Local Ollama judge generation timed out") from error
        except HTTPError as error:
            raise JudgeProviderError(f"Local Ollama judge returned HTTP {error.code}") from error
        except (URLError, ConnectionError, ValueError) as error:
            raise JudgeProviderError("Local Ollama judge generation failed") from error
        return JudgeProviderResponse(value["response"], {
            "provider": self.provider_name,
            "model": request.config.model,
            "model_digest": digest,
            "methodology_version": request.config.methodology_version,
            "prompt_version": request.config.prompt_version,
            "rubric_version": request.config.rubric_version,
            "temperature": request.config.temperature,
            "seed": request.config.seed,
            "elapsed_ms": (perf_counter() - started) * 1000,
            "raw_response_metadata": {key: value.get(key) for key in ("created_at", "total_duration", "load_duration", "eval_duration", "prompt_eval_duration", "done_reason")},
            "measurement_semantics": "Layer 2 judge output is a structured measurement, not ground truth or calibrated probability",
        })
