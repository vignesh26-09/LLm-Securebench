# Phase 12 dashboard implementation

## Continuation status — September 10, 2026

The approved read-only API extension and dashboard continuation are documented in `DASHBOARD_BACKEND_CONTINUATION.md`. That report supersedes the original endpoint-unavailable limitations below; those paragraphs describe the previous implementation boundary.

## Original phase status

The Phase 12 frontend is implemented as a research-oriented React and TypeScript application in `frontend/`. It is an evidence browser, not a scientific scoring or claim-making layer. Its production build, type checking, linting, frontend tests, and the Phase 11 API contract smoke tests are required before marking the phase complete.

## Actual API contract consumed

The dashboard was reconciled against `apps/api/main.py`, rather than example paths in the original dashboard design document. It makes live requests only to:

- `GET /health`
- `GET /ready`
- `GET /scientific-records?family=&limit=&offset=`

`/scientific-records` is the generic, paginated source for persisted scientific records. The UI preserves its family, schema version, scope, scientific status, payload, and provenance. The configured UI page size is an engineering setting (`VITE_SECURELLM_PAGE_SIZE`, default `25`), not a scientific constant.

The following requested integrations are not provided by Phase 11 and are shown as **BACKEND ENDPOINT UNAVAILABLE**, without an API request or silent demo substitution: models, datasets, benchmark runs, evaluation results, linked Layer 1/Layer 2 evidence, and model comparison. The UI does not make up routes such as `/models`, `/datasets`, or `/metrics/...`.

## Architecture

```
React pages and shared components
        ↓
typed view/state boundary
        ↓
native fetch API client
        ↓
Phase 11 FastAPI routes
```

The frontend uses React, TypeScript, Vite, React Router, TanStack Query, and Apache ECharts. It intentionally uses native `fetch`; Axios is not a dependency. The development server proxies only the three real API routes to the local FastAPI service. Production deployments use same-origin routing or a configured `VITE_SECURELLM_API_BASE_URL`.

## Scientific-integrity safeguards

- The UI keeps loading, successful scientific null/undefined, 404/not present, and backend/API failures as distinct states.
- BSDA is rendered only as independently named component evidence. No composite score is introduced. Uncertainty is visible only when present upstream.
- Recovery Capability uses only lossless `rc` record payloads. No typed fields, trajectories, latency threshold, or recovery outcome is inferred.
- SAEA calls `CV_obs` **observed cumulative vulnerability**. It never calls it a coefficient of variation, never calls it attack success, and does not impose a frontend sequence-length rule or reinterpret recovery diagnostics.
- DRAA pages expose only Mode A/B evidence and uncalibrated diagnostics. Mode C and scalar risk values are not offered.
- PRI remains descriptive and profile-oriented: no scalar, ranking, or qualitative robustness grade is generated.
- DQI is explicitly marked **EXPLORATORY / NOT SCIENTIFICALLY VALIDATED**.
- ML and statistical pages render only persisted source-native artifacts; they do not fabricate validation conclusions, p-values, effect sizes, confidence intervals, ROC curves, or calibration results.
- Scientific maturity is a source status where available; otherwise the UI uses the conservative label **NOT VALIDATED**. It does not assert a validation phase.

## UI pages

The shell includes Overview; Models; Datasets; Benchmark Runs; Evaluation Results; Security Analysis; BSDA; Recovery Capability; SAEA; DRAA; PRI; DQI; ML Prediction; Statistical Analysis; Model Comparison; and Experiment Details. Metric, ML, statistics, and Experiment Details views query the generic scientific-record endpoint with an optional family filter. Pages without an actual endpoint state why their data cannot be shown.

## Verification checklist

The original design checklist was reconciled to unchecked work before this implementation. The following items are marked complete only after their corresponding verification has finished:

- [x] 12A: Vite/React/TypeScript scaffold, environment example, lint and typecheck
- [x] 12B: shell, route navigation, native-fetch API client, health/readiness display
- [x] 12C: status, provenance, loading, error, empty, unavailable, table and pagination components
- [x] 12D: Phase-11-backed overview and generic record browser; unavailable core pages are explicit
- [x] 12E: metric pages preserving BSDA/RC/SAEA/DRAA/PRI/DQI boundaries
- [x] 12F: ML/statistical artifact views without generated statistics
- [x] 12G: ECharts wrapper with local error containment; it renders only supplied numeric data
- [x] 12H: unit, API integration, scientific-integrity tests, lint, typecheck, and production build checks

## Local commands

```powershell
cd F:\SecureLLM\frontend
npm install --cache .npm-cache
npm run dev
npm run typecheck
npm run lint
npm run test
npm run build
```

For the backend contract and whole repository:

```powershell
cd F:\SecureLLM
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
& .\.venv\Scripts\python.exe -m scripts.smoke_check
& .\.venv\Scripts\python.exe -m scripts.api_smoke
```

## Known limitations and next work

Phase 11 intentionally has no public model, dataset, run, evaluation, or linked-evidence read routes. Adding them requires an approved Phase 11 API extension and must preserve append-only history, provenance, statuses, nulls, and the existing scientific STOP rules. The frontend must not compensate for missing contracts with inferred data or science.
