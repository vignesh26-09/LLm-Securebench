# Phase 11 backend/API implementation reconciliation

## 1. Executive decision
Phase 11 may add persistence, service, and API adapters around existing contracts without reorganizing scientific modules or making scientific claims. Typed ORM mapping is limited to actual dataclasses. RC is **BLOCKED_FOR_TYPED_MAPPING** because there is no typed runtime object; persist a lossless versioned payload only.

## 2. Gemini items approved unchanged
Layered API → service → repository → ORM separation, parameterized ORM access, strict schemas, safe errors, request IDs, secret-safe structured logs, and allowlisted filtering/sorting are approved engineering patterns.

## 3. Gemini items approved with modification
FastAPI, SQLAlchemy, Pydantic, Alembic, PostgreSQL, and SQLite are future implementation choices, not current facts. API write operations are internal/development boundaries until authentication is approved. Scientific records are append-only.

## 4. Gemini items rejected
Reject alternate metric expansions, BSDA composite, RC “Robustness Score”, DRAA fabricated fields/risk score, PRI prompt-risk/ranking semantics, Layer 2 probability interpretation, unsupported ML models/calibration, automatic claim validation, HTTP 530, PostgreSQL-only declarations, public unrestricted evidence mutation, DELETE, and cascade lifecycle.

## 5. Actual repository integration points
Adapters integrate with `core.dataset`, `core.benchmark`, `core.detection`, `core.judging`, `core.metrics.bsda`, `core.saea`, `core.draa`, `core.pri`, `core.prediction`, and `core.statistics`. Existing dataclasses remain scientific contracts.

## 6. Dependency decision
Future minimum dependencies, only when implementation is separately approved: FastAPI, SQLAlchemy 2.x, Pydantic, and Alembic. Keep unittest; do not add pytest. Pool/page/payload/version numbers are configurable engineering settings, not scientific thresholds.

## 7. Sync/async decision
Use synchronous SQLAlchemy initially, matching current synchronous engines. Reconsider async only with demonstrated need.

## 8. SQLAlchemy strategy
Use portable SQLAlchemy 2.x declarative entities. Repositories do not commit; services own transaction boundaries. ORM entity ≠ scientific object ≠ API schema.

## 9. Alembic strategy
Alembic is IMPLEMENT_WITH_MODIFICATION for immutable schema migrations, never scientific-meaning rewrites.

## 10. PostgreSQL/SQLite strategy
Use portable JSON with a PostgreSQL JSONB variant. SQLite is an engineering test dialect, not PostgreSQL proof. PostgreSQL integration tests are deferred.

## 11. ORM/domain/schema separation
Use adapters around actual scientific dataclasses. Where no typed runtime exists, store a lossless payload plus family/schema/metric version; do not create duplicate domain classes.

## 12. Final entity model
Candidate identities: Dataset, immutable DatasetVersion, ModelConfig, BenchmarkRun, EvaluationResult, Layer1Result, Layer2Result, ResearchMetricResult, MLExperimentArtifact, StatisticalExperimentArtifact, ScientificReviewRecord.

## 13. Final relationship model
DatasetVersion belongs to Dataset and is unique by `(dataset_id, version)`; content hash/provenance are optional. BenchmarkRun links DatasetVersion/ModelConfig; EvaluationResult links run. Evidence has one explicit scope and cannot conflict with derivable ancestry.

## 14. Final metric persistence contracts
Persist source-native payloads with explicit metric family, metric version, schema version, status, and provenance. Necessary scopes: EVALUATION, SESSION_SEQUENCE, BENCHMARK_RUN, MODEL_CONFIGURATION, DATASET_VERSION.

## 15. RC typed-mapping status
**BLOCKED_FOR_TYPED_MAPPING**. Lossless structured payload only; no invented raw/bounded scores, clipping, or applicability fields.

## 16. DRAA mapping
Persist `DRAAEvidenceRecord` and `EvidenceFeature` losslessly. Mode A/B risk score is null; Mode C is deferred.

## 17. PRI mapping
Persist `PRIProfileRecord`, cells, coverage, identity, and provenance losslessly. Scalar PRI remains null and rankings are excluded.

## 18. ML mapping
Persist actual Phase 9 schemas and prevalence/native L2-logistic engineering artifacts only. Preserve independent engineering, label, validation, and calibration status; synthetic means engineering-only.

## 19. Statistical mapping
Persist generic `StatisticalResultRecord` and computed payloads losslessly. Do not imply p-values, general intervals, hierarchical models, or claim validation.

## 20. Scientific review workflow
No generic PATCH for claim validation. A dedicated review operation creates a `ScientificReviewRecord` with evidence/reviewer/protocol/decision/rationale/scope/provenance; statistics never derive the decision.

## 21. Immutability
Evaluation, evidence, metric, ML, and statistical records are append-only. Corrections create superseding/versioned records or review metadata.

## 22. Deletion/cascade policy
Use RESTRICT/NO ACTION for scientific history. No public DELETE endpoints. Development cleanup is a separate lifecycle.

## 23. Transaction policy
Service opens, commits, and rolls back one transaction; repositories only query/add. Session dependencies must not commit independently.

## 24. API write/read surface
Safe initial surface: health/readiness GET and paginated result GET; internal service writes. Authenticated ingestion is future. Development fixture writes must be explicitly internal.

## 25. Pagination/filtering/sorting
Use configured bounds, validated pagination, and allowlisted identity/status/version fields; never interpolate user SQL.

## 26. Errors
Return stable code/message/request ID; separate validation from dependency failures and never expose traces/secrets/payloads.

## 27. Logging/request IDs
Generate/propagate request IDs. Logs omit prompts, secrets, and unsafe evidence.

## 28. Health/readiness
Health reports liveness. Readiness checks DB: 200 ready, 503 unavailable.

## 29. Configuration
Database URL/dialect, pools, paging, payloads, and logging are configuration parameters.

## 30. Tests
Future tests cover SQLite mappings, lossless round trips, append-only/restrict behavior, invariant rejection, errors/request IDs, ready 200/503, plus optional PostgreSQL integration.

## 31. Smoke
Future smoke uses internal fixture-service writes and readback/provenance only; it must not require public evidence mutation.

## 32. Implementation stages
Dependencies/config; portable persistence/services; read-only API/health; explicit review workflow; optional authenticated ingestion; optional PostgreSQL integration.

## 33. Blockers
Typed RC, Phase 10C outputs, DRAA Mode C, PRI scalar/ranking, real ML validation, authentication policy, exact dependency approval, and production lifecycle policy remain blocked/deferred.

## 34. Exact scientific integrity guarantees
The backend cannot create BSDA composite, DRAA risk, PRI scalar, universal attack success, RC threshold, SAEA replacement estimator, Layer 2 probability, or automatic claim validation. It preserves source-native status, applicability, uncertainty, provenance, and null values.

## Final decision matrix

| Feature | Decision |
| --- | --- |
| FastAPI, SQLAlchemy 2.x, Pydantic, PostgreSQL, SQLite tests, Alembic | IMPLEMENT_WITH_MODIFICATION |
| sync DB model, ORM/domain/schema separation, ScientificReviewRecord, pagination/filtering/sorting, request IDs, health/readiness | IMPLEMENT_NOW |
| Dataset, DatasetVersion, ModelConfig, BenchmarkRun, EvaluationResult, Layer1/Layer2, BSDA/SAEA, DRAA/PRI/ML/statistical persistence | IMPLEMENT_WITH_MODIFICATION |
| RC typed mapping | BLOCKED |
| public result POST, DELETE endpoints, cascade deletion, authentication, PostgreSQL integration tests | DEFER |
