# Phase 2 provider and trust-boundary audit — 2026-10-14

**Scope and authorization.** The user's 2026-10-14 “Accelerated Feasibility Pilot” request separately authorizes a **limited engineering feasibility continuation** while G1 remains stopped for research-originality claims. This audit used only installed-model metadata: `ollama list`, `ollama --version`, Ollama `/api/tags` and `/api/show`, and `scripts/feasibility_provider_audit.py`. It made **zero** `/api/chat` or `/api/generate` calls, downloaded no weights, and produced no pilot observations. A live harmless provider probe and all real pilot calls remain separately gated.

## Read-only identities and static template evidence

| Model | Installed digest (`/api/tags`) | Family / quantization | SHA-256 of `/api/show` static template | Static role finding |
|---|---|---|---|---|
| `qwen3.5:2b` | `324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df` | qwen35 / Q8_0 | `b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315` | Template is `{{ .Prompt }}` with Qwen-specific renderer; role serialization is not visible in the static template. |
| `gemma3:4b` | `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` | gemma3 / Q4_K_M | `e0a42594d802e5d31cdc786deb4823edb8adff66094d49de8fffe976d753e348` | Static template serializes both `system` and `user` messages as `<start_of_turn>user` turns. A sent `system` role must **not** be assumed to have distinct trusted priority after rendering. |

Installed Ollama version: **0.40.3**. Both `/api/show` parameter strings declare `top_p 0.95`, but that is a static model default, not proof of an effective value in a particular generation. Neither endpoint returns the fully rendered prompt for a future `/api/chat` request or proof that the protected instruction and exposure history remain in effective context.

The adapter at `core/inference/ollama_provider.py::OllamaProvider.generate_conversation` sends an ordered `messages` array to `/api/chat`, prepending `system_prompt` with role `system`. It requests temperature, seed, output cap (`num_predict`), optional explicit top-p, and `num_ctx` when `ModelMetadata.context_window` is set. `generate` uses `/api/generate` with the same generation controls except `num_ctx`. The response metadata records the **requested** options and `effective_options=None`: Ollama's ordinary generation response does not echo effective generation controls. Existing `effective_seed` fields are the locally selected/transported seed, not independent provider acknowledgement; no scientific record should treat them as a measured effective seed. The model digest comes from supplied model metadata and must be checked against `/api/tags` at a future preflight, not presumed current forever.

## Scientific context status

`core/feasibility_pilot/context.py::assess_context` keeps scientific `retained_verified`, `truncated_known`, and `retention_unverifiable` separate from the older request-level `ContextValidity`. `retained_verified` requires an evidence reference **and** affirmative post-template required-content presence **and** effective-retention confirmation. Known loss or an effective-limit exceedance yields `truncated_known`. Anything else remains `retention_unverifiable`; ordered message delivery, token counts, nominal `num_ctx`, and canary success cannot upgrade it. Asymmetric A/T statuses trigger a pair-validity warning. Given today's read-only Ollama evidence, **both models are `rendered_prompt_unverified` and `retention_unverifiable`**. No context-valid primary population can be asserted on this evidence alone.

## Verification and unresolved gate items

- `F:\SecureLLM\.venv\Scripts\python.exe scripts/feasibility_provider_audit.py` reproduced the two digests and template hashes above from read-only metadata.
- `F:\SecureLLM\.venv\Scripts\python.exe -m pytest tests/test_feasibility_provider_audit.py tests/test_feasibility_provider_options.py tests/test_feasibility_context.py tests/test_inference.py -q`: **15 passed**.
- No harmless live rendering probe was authorized or run. Even such a probe would not by itself establish effective retention or Gemma system-priority equivalence. The team must decide whether the observed provider evidence can support the planned trusted-secret threat model; until then C3 and context-valid effects are unavailable.
- G2 also requires approved restricted storage, retry/failure rules, and arm/distance/token-control choices in `implementation_decisions.md`. They are not yet approved. This is an engineering gate stop, not a claim that the research hypothesis is false.
