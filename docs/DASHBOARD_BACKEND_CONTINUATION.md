# Backend and dashboard continuation — 2026-09-10

## Follow-up: unavailable metric and model views

The subsequent UI repair restored stopped local services and added `scripts/start_local.ps1` for repeatable startup with health, readiness, proxy and HTML verification. API status now refreshes every 15 seconds and provides a retry control. Missing data is explained per resource/metric instead of implying a missing endpoint. Unknown dashboard URLs show a page-not-found view. Neutral/missing status styling no longer classifies an unknown status as unavailable. Scientific-record pagination retains its Previous control on an empty trailing page.

Model comparison now supports selecting up to three persisted configurations across pages and comparing their actual payload settings, preserving null versus missing values and linking to runs. No real model configuration exists in the repository database; the view explicitly reports that prerequisite rather than inventing one. Scientific performance comparison remains deferred.

The existing `calculate_dqi` implementation was run on the normalized repository example using `scripts/analyze_repository_example.py`. This is a newly computed engineering diagnostic, not an imported historical scientific result. The immutable artifact retains source and code hashes, default weights, normalization identity, dataset-version scope and explicit example/nonvalidated provenance. No embeddings were supplied; novelty's zero is the existing implementation default, not a semantic measurement. DQI now displays the resulting components and source score (approximately 0.7369), with these limitations visible. Repeating the command created no duplicate. No other metric artifacts or model configurations were generated.

Current database counts supersede the initial table below: **1 dataset, 1 version, 1 scientific record (DQI); every other entity count remains 0**. Other special metrics still require legitimate evaluation/session/profile artifacts and retain their scientific restrictions.

Follow-up verification: **94 Python tests, 18 frontend tests, typecheck, lint, production build and API smoke passed**. Live health/readiness/models/DQI/summary requests passed directly and through the frontend proxy; affected page routes served HTML. Both local services were verified running. Browser screenshot QA remains unverified.

This implementation extends the approved Phase 11 read surface around existing ORM entities. No scientific algorithm, metric definition, scientific threshold, or claim-validation rule was changed. Existing uncommitted work was retained.

## Endpoints

New paginated GET collections and GET `/{record_id}` details:

- `/datasets`
- `/dataset-versions`
- `/models`
- `/benchmark-runs`
- `/evaluations`
- `/layer1-results`
- `/layer2-results`
- `/scientific-reviews`

Also added GET `/dashboard-summary` (actual database counts) and GET `/scientific-records/{record_id}` (lossless record including owner, scope, schema, status and provenance). Existing `/health`, `/ready` and `/scientific-records` contracts remain available.

New collections return `items`, `total`, `limit`, `offset`. Pagination is bounded to 1–100 records; offset is nonnegative. `filter_by`/`value` permit only declared identity/status fields that exist on the entity. Sort is restricted to `id` or `created_at`, with `asc`/`desc` direction and deterministic ID tie breaking. SQLAlchemy binds filter values. Missing details return 404; database errors return a safe 503; responses carry request IDs. Model configuration and provider metadata credential keys are redacted recursively in API projections. This redaction does not modify persisted evidence.

No new public writes or deletes were added. The pre-existing internal scientific-review POST remains a local development boundary; authentication and production exposure remain deferred.

## Imported data and provenance

Only `data/raw/example.json` was imported, after validation through the existing `JsonDatasetLoader`. The importer is `python -m scripts.import_repository_data`. It stores the original parsed JSON, including all three example prompts without normalization, in one immutable dataset-version payload. It does not run inference or calculate metrics.

- Dataset ID: `repository:example`
- Source version: `0.1.0`
- SHA-256: `b395724a958530e590e2800a9a3c351fb702c6bb0b36327cb81070d0b8375c1c`
- Provenance kind: `repository_example`
- Scientific validation: explicitly false
- Second import: no changes; same content identity

The input is an existing engineering example, not a validated research corpus. `data/external`, `data/interim`, and `data/processed` contain only placeholders. `experiments` contains documentation. `configs/base.yaml` is a benchmark-name placeholder, not a model configuration. Test/smoke fixtures and specification examples were not imported as research findings. The database was empty before import.

| Database entity | Count |
| --- | ---: |
| Datasets | 1 |
| Dataset versions | 1 |
| Model configurations | 0 |
| Benchmark runs | 0 |
| Evaluation results | 0 |
| Layer 1 results | 0 |
| Layer 2 results | 0 |
| Scientific records | 0 |
| Scientific reviews | 0 |

The three source records are embedded in the dataset-version payload; they are not evaluation results.

## Dashboard

Overview now displays database totals. Models, Datasets, Dataset versions, Benchmark runs, Evaluation results, Security analysis/Layer 1, Layer 2 and Scientific reviews query the corresponding read endpoints. Links carry explicit foreign-key filters from dataset to versions, model/version to runs, run to evaluations, and evaluation to each evidence layer. Stored rows can be inspected with source payload and provenance. Pagination uses server totals. Loading, empty, missing and API-error states remain separate.

The model-comparison page reads model configurations only; comparable outcomes, ranking and scientific comparison are still unavailable. Metric, ML, statistical and experiment-details pages retain their existing scientific-record reads. Their empty state reflects absent persisted artifacts, not absent read routes.

The UI uses a light sidebar, restrained green accents, spacious cards, clearer typography, visible focus indicators and responsive layouts. HTML browser navigation and JSON API fetches are distinguished in the Vite proxy, including shared paths such as `/models` and `/datasets`. The typecheck command now checks referenced TypeScript projects.

## Verification

- Python: **93 tests passed**, full `unittest discover -s tests -p "test_*.py"`.
- Frontend: **14 tests passed** across four files.
- Typecheck, ESLint with zero allowed warnings, and production build: **passed**.
- Smoke scripts: `smoke_check`, `api_smoke`, `end_to_end_smoke`, `draa_smoke`, `prediction_smoke`, `pri_smoke`, `saea_smoke`, `statistics_smoke`: **passed**. Engineering smoke outputs were not imported.
- Live HTTP: 12 API paths returned 200 directly and through Vite, including request IDs; 19 dashboard navigation paths returned HTML.
- Source import: validated, hash recorded, lossless payload tested, second import confirmed idempotent.
- Backend restarted at `http://127.0.0.1:8000` using the workspace virtual-environment launcher. Frontend restarted at `http://127.0.0.1:5173`, with strict port binding.
- TEMP/TMP for command executions: `F:\SecureLLM.tmp`; Python tempfile creation and cleanup passed. Implementation files and service logs remain in the project workspace. Logs are under `.tmp/`.
- Existing dependency warnings: Starlette/httpx deprecation and React Router future flags. No test or build failure remains.
- Visual screenshot QA was not completed: automatic approval review rejected the headless-browser launch command as “blocked by policy,” without further explanation. HTTP navigation checks and component tests passed; these do not constitute visual browser verification.

## Scientific integrity and remaining limitations

BSDA remains component evidence; RC remains lossless/untyped; SAEA retains observed cumulative vulnerability semantics; DRAA Mode A/B risk and PRI scalar remain null; Layer 2 scores are not probabilities; DQI remains exploratory. No scientific results, confidence intervals, rankings, validation claims or new research definitions were generated. Existing scientific mapping and integrity tests passed.

Scientific pages require legitimate persisted results. Typed RC, DRAA Mode C, PRI scalar/ranking, deferred hierarchical inference and real ML calibration/validation remain outside the approved scientific scope. Public authenticated ingestion, benchmark execution from the UI, PostgreSQL integration verification and production lifecycle/authentication remain unavailable. No new methodology ambiguity blocked this implementation.
