"""Optional local Hugging Face Transformers provider, CPU-safe by default."""

import logging
from time import perf_counter

from core.inference.contracts import InferenceError, InferenceRequest, InferenceResult, InferenceTimeoutError, TokenUsage

logger = logging.getLogger(__name__)


class LocalTransformersProvider:
    """Generates from an already-local model; never downloads model assets automatically."""

    provider_name = "local-transformers"

    def __init__(self, model_path: str, *, device: str = "cpu", local_files_only: bool = True) -> None:
        self._model_path = model_path
        self._device = device
        self._local_files_only = local_files_only
        self._model: object | None = None
        self._tokenizer: object | None = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise InferenceError("Install optional local inference dependencies: pip install -e '.[transformers]'") from error
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_path, local_files_only=self._local_files_only)
            self._model = AutoModelForCausalLM.from_pretrained(self._model_path, local_files_only=self._local_files_only)
            self._model.to(self._device)
            self._model.eval()
        except Exception as error:
            raise InferenceError(f"Unable to load local Transformers model '{self._model_path}'") from error

    def generate(self, request: InferenceRequest) -> InferenceResult:
        if request.generation.top_p is not None:
            raise InferenceError("Explicit top_p is unsupported by this local Transformers adapter")
        self._load()
        assert self._model is not None and self._tokenizer is not None
        started = perf_counter()
        try:
            inputs = self._tokenizer(request.prompt, return_tensors="pt")
            inputs = {key: value.to(self._device) for key, value in inputs.items()}
            generated = self._model.generate(
                **inputs,
                max_new_tokens=request.generation.resolved_max_new_tokens,
                do_sample=request.generation.temperature > 0,
                temperature=request.generation.temperature if request.generation.temperature > 0 else None,
            )
            elapsed = perf_counter() - started
            if request.generation.timeout_seconds is not None and elapsed > request.generation.timeout_seconds:
                raise InferenceTimeoutError(f"Local generation exceeded timeout of {request.generation.timeout_seconds} seconds")
            input_tokens = int(inputs["input_ids"].shape[-1])
            output_tokens = int(generated.shape[-1]) - input_tokens
            text = self._tokenizer.decode(generated[0][input_tokens:], skip_special_tokens=True)
        except InferenceTimeoutError:
            raise
        except Exception as error:
            logger.exception("Local Transformers inference failed for model %s", request.model.name)
            raise InferenceError(f"Local Transformers inference failed for model '{request.model.name}'") from error
        logger.debug("Local Transformers inference completed for model %s", request.model.name)
        return InferenceResult(
            text=text, model=request.model, provider=self.provider_name, latency_ms=elapsed * 1000,
            token_usage=TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens),
            finish_reason="length", metadata={"model_path": self._model_path, "device": self._device},
        )
