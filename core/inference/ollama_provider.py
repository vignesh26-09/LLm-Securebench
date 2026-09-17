"""Local Ollama adapter. Uses installed models only; never pulls model weights."""
import json
import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from core.inference.contracts import (ContextValidity, ConversationRequest,
    ConversationResponse, InferenceError, InferenceTimeoutError, InferenceResult, TokenUsage)

ENDPOINT = 'http://127.0.0.1:11434'


def installed_models():
    try:
        with urlopen(ENDPOINT + '/api/tags', timeout=5) as response:
            return json.load(response)['models']
    except (OSError, ValueError, KeyError) as exc:
        raise InferenceError('Local Ollama is unreachable or returned invalid model metadata') from exc


class OllamaProvider:
    provider_name = 'ollama-local'

    def __init__(self, *, seed=2026):
        self.seed = seed

    def generate(self, request):
        seed = request.requested_seed if request.requested_seed is not None else self.seed
        options = {'temperature': request.generation.temperature,
                   'num_predict': request.generation.resolved_max_new_tokens, 'seed': seed}
        body = {'model': request.model.name, 'prompt': request.prompt, 'stream': False,
                'options': options, 'keep_alive': '5m'}
        if 'thinking' in request.model.capabilities:
            body['think'] = False
        started = perf_counter()
        try:
            with urlopen(Request(ENDPOINT + '/api/generate', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}),
                         timeout=request.generation.timeout_seconds or 180) as response:
                value = json.load(response)
            if value.get('done') is not True or not isinstance(value.get('response'), str):
                raise InferenceError('Ollama returned an incomplete or invalid response')
            counts = [value.get('prompt_eval_count'), value.get('eval_count')]
            if any(v is not None and (type(v) is not int or v < 0) for v in counts):
                raise InferenceError('Ollama returned invalid token counts')
        except (TimeoutError, socket.timeout) as exc:
            raise InferenceTimeoutError('Local Ollama generation timed out') from exc
        except HTTPError as exc:
            raise InferenceError(f'Local Ollama returned HTTP {exc.code}') from exc
        except (URLError, ValueError) as exc:
            raise InferenceError('Local Ollama generation failed') from exc
        return InferenceResult(value['response'], request.model, self.provider_name,
            (perf_counter() - started) * 1000,
            TokenUsage(*counts, sum(counts) if all(v is not None for v in counts) else None),
            value.get('done_reason'),
            {**{key: value.get(key) for key in ('model', 'created_at', 'total_duration', 'load_duration', 'eval_duration', 'prompt_eval_duration')},
             'options': options, 'thinking_enabled': body.get('think'), 'model_digest': request.model.version,
             'requested_seed': request.requested_seed, 'effective_seed': seed, 'provider_supports_seed': True})

    def generate_conversation(self, request: ConversationRequest) -> ConversationResponse:
        seed = request.requested_seed if request.requested_seed is not None else self.seed
        messages = []
        if request.system_prompt:
            messages.append({'role': 'system', 'content': request.system_prompt})
        messages.extend({'role': item.role, 'content': item.content} for item in request.messages)
        options = {'temperature': request.generation.temperature,
                   'num_predict': request.generation.resolved_max_new_tokens, 'seed': seed}
        if request.model.context_window is not None:
            options['num_ctx'] = request.model.context_window
        body = {'model': request.model.name, 'messages': messages, 'stream': False,
                'options': options, 'keep_alive': '5m'}
        if 'thinking' in request.model.capabilities:
            body['think'] = False
        started = perf_counter()
        try:
            with urlopen(Request(ENDPOINT + '/api/chat', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'}),
                         timeout=request.generation.timeout_seconds or 180) as response:
                value = json.load(response)
            text = value['message']['content']
            if value.get('done') is not True or not isinstance(text, str):
                raise InferenceError('Ollama returned an incomplete or invalid conversation response')
        except (TimeoutError, socket.timeout) as exc:
            raise InferenceTimeoutError('Local Ollama conversation generation timed out') from exc
        except HTTPError as exc:
            raise InferenceError(f'Local Ollama returned HTTP {exc.code}') from exc
        except (URLError, ValueError, KeyError, TypeError) as exc:
            raise InferenceError('Local Ollama conversation generation failed') from exc
        input_tokens = value.get('prompt_eval_count')
        output_tokens = value.get('eval_count')
        total = input_tokens + output_tokens if isinstance(input_tokens, int) and isinstance(output_tokens, int) else None
        if request.model.context_window is None or not isinstance(input_tokens, int):
            context_status = ContextValidity.UNKNOWN
            context_reason = 'model_context_window_or_prompt_token_count_unavailable'
        elif input_tokens <= request.model.context_window:
            context_status = ContextValidity.RETAINED
            context_reason = 'complete_ordered_history_sent_and_prompt_tokens_within_declared_context_window'
        else:
            context_status = ContextValidity.TRUNCATED
            context_reason = 'provider_prompt_tokens_exceed_declared_context_window'
        return ConversationResponse(
            text, request.conversation_id, request.messages[-1].turn_index, request.model,
            self.provider_name, (perf_counter() - started) * 1000, context_status,
            TokenUsage(input_tokens, output_tokens, total), value.get('done_reason'),
            request.requested_seed, seed, True,
            {'model': value.get('model'), 'created_at': value.get('created_at'),
             'model_digest': request.model.version, 'options': options,
             'message_count': len(messages), 'context_reason': context_reason,
             'complete_ordered_history_sent': True},
        )
