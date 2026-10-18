# Architecture

SecureLLMBench follows a ports-and-adapters style of clean architecture.

- `core` owns domain types, use-case boundaries, and abstract ports.
- `apps` provides delivery mechanisms such as the future HTTP API.
- Adapter implementations belong at the outer edge and may depend on `core`.
- `core` must not depend on a web framework, an LLM SDK, a database, or a
  particular dataset format.

The initial interfaces are intentionally narrow. Add a concrete adapter only when
there is a supported integration to implement and cover it with tests.
