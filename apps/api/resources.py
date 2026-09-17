"""Read-only projections of existing persistence entities; no derived science."""
from fastapi import HTTPException, Query
from sqlalchemy import func, select
from core.persistence import models


RESOURCES = {
    "datasets": models.DatasetEntity,
    "dataset-versions": models.DatasetVersionEntity,
    "models": models.ModelConfigEntity,
    "benchmark-runs": models.BenchmarkRunEntity,
    "evaluations": models.EvaluationResultEntity,
    "layer1-results": models.LayerOneResultEntity,
    "layer2-results": models.LayerTwoResultEntity,
    "scientific-reviews": models.ScientificReviewEntity,
}
FILTERS = {"id", "dataset_id", "version", "model_name", "model_config_id",
           "dataset_version_id", "status", "benchmark_run_id", "case_id",
           "execution_status", "evaluation_result_id", "detector_name", "dimension",
           "claim_id", "evidence_bundle_id", "decision"}


def redact_configuration(value):
    """Configuration and provider metadata may contain credentials."""
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if any(part in key.lower() for part in
                ("secret", "token", "password", "api_key", "apikey", "authorization", "credential"))
                else redact_configuration(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_configuration(item) for item in value]
    return value


def project(row):
    result = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    if isinstance(row, models.ModelConfigEntity):
        result["payload"] = redact_configuration(result["payload"])
    if isinstance(row, models.EvaluationResultEntity):
        result["provider_metadata"] = redact_configuration(result["provider_metadata"])
    return result


def register_resources(app, factory):
    @app.get("/dashboard-summary")
    def summary():
        with factory() as session:
            entities = {**RESOURCES, "scientific-records": models.ScientificRecordEntity}
            counts = {name: session.scalar(select(func.count()).select_from(entity))
                      for name, entity in entities.items()}
            counts["model-scores"] = session.scalar(select(func.count()).select_from(models.ScientificRecordEntity).where(models.ScientificRecordEntity.family == "model_score"))
            return {"counts": counts}

    @app.get("/model-scores")
    def model_scores(limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0),
                     sort: str = "created_at", direction: str = "desc"):
        if sort not in {"id", "created_at"} or direction not in {"asc", "desc"}:
            raise HTTPException(422, "Invalid sort")
        statement = select(models.ScientificRecordEntity).where(models.ScientificRecordEntity.family == "model_score")
        with factory() as session:
            total = session.scalar(select(func.count()).select_from(statement.subquery()))
            column = getattr(models.ScientificRecordEntity, sort)
            rows = session.scalars(statement.order_by(column.desc() if direction == "desc" else column.asc(),
                                                      models.ScientificRecordEntity.id).limit(limit).offset(offset))
            items = []
            for row in rows:
                payload = row.payload
                items.append({
                    "id": row.id,
                    "run_id": payload.get("run_id"),
                    "model_name": payload.get("model_name"),
                    "status": _model_score_status(row.status, payload),
                    "model_score": payload.get("model_score"),
                    "mean_threat_score": payload.get("mean_threat_score"),
                    "worst_case_threat_score": payload.get("worst_case_threat_score"),
                    "coverage": payload.get("coverage"),
                    "completed_evaluations": payload.get("completed_evaluations"),
                    "total_evaluations": payload.get("total_evaluations"),
                    "formula_version": payload.get("formula_version"),
                    "formula": payload.get("formula"),
                    "warnings": payload.get("warnings", []),
                    "created_at": row.created_at,
                    "provenance": redact_configuration(row.provenance),
                })
            return {"items": items, "total": total, "limit": limit, "offset": offset}

    @app.get("/benchmark-runs/{run_id}/report")
    def benchmark_run_report(run_id: str):
        """Return a read-only operational report from persisted run evidence.

        This is deliberately a projection: it reports execution and detector
        observations without converting them into attack outcomes or a safety
        recommendation.
        """
        with factory() as session:
            run = session.get(models.BenchmarkRunEntity, run_id)
            if run is None:
                raise HTTPException(404, "Benchmark run not found")
            model = session.get(models.ModelConfigEntity, run.model_config_id)
            evaluations = list(session.scalars(select(models.EvaluationResultEntity).where(
                models.EvaluationResultEntity.benchmark_run_id == run_id
            ).order_by(models.EvaluationResultEntity.created_at, models.EvaluationResultEntity.id)))
            evaluation_ids = [row.id for row in evaluations]
            layer_rows = list(session.scalars(select(models.LayerOneResultEntity).where(
                models.LayerOneResultEntity.evaluation_result_id.in_(evaluation_ids)
            ))) if evaluation_ids else []
            score_record = session.scalar(select(models.ScientificRecordEntity).where(
                models.ScientificRecordEntity.family == "model_score",
                models.ScientificRecordEntity.owner_id == run_id,
            ).order_by(models.ScientificRecordEntity.created_at.desc()))

            completed = sum(row.execution_status == "completed" for row in evaluations)
            failed = len(evaluations) - completed
            latencies = [row.latency_ms for row in evaluations if row.latency_ms is not None]
            by_evaluation: dict[str, list[models.LayerOneResultEntity]] = {}
            for row in layer_rows:
                by_evaluation.setdefault(row.evaluation_result_id, []).append(row)
            detector_summary: dict[str, dict[str, object]] = {}
            for row in layer_rows:
                item = detector_summary.setdefault(row.detector_name, {"detector": row.detector_name, "max_score": 0.0, "observed_signal_count": 0})
                item["max_score"] = max(float(item["max_score"]), row.score)
                if row.score > 0:
                    item["observed_signal_count"] = int(item["observed_signal_count"]) + 1
            cases = []
            for evaluation in evaluations:
                signals = [
                    {"detector": signal.detector_name, "score": signal.score, "confidence": signal.confidence}
                    for signal in by_evaluation.get(evaluation.id, []) if signal.score > 0
                ]
                cases.append({
                    "id": evaluation.id,
                    "case_id": evaluation.case_id,
                    "execution_status": evaluation.execution_status,
                    "latency_ms": evaluation.latency_ms,
                    "finish_reason": evaluation.provider_metadata.get("finish_reason"),
                    "response_available": evaluation.response is not None,
                    "observed_detector_signals": signals,
                })
            payload = score_record.payload if score_record else {}
            coverage = payload.get("coverage", completed / len(evaluations) if evaluations else 0.0)
            return {
                "run": {"id": run.id, "status": run.status, "model_name": model.model_name if model else None,
                        "model_config_id": run.model_config_id, "created_at": run.created_at},
                "execution": {"total_cases": len(evaluations), "completed_cases": completed, "failed_cases": failed,
                              "coverage": coverage, "mean_latency_ms": sum(latencies) / len(latencies) if latencies else None},
                "detector_summary": sorted(detector_summary.values(), key=lambda item: str(item["detector"])),
                "cases": cases,
                "model_score": {
                    "status": _model_score_status(score_record.status, payload) if score_record else "not_computed",
                    "value": payload.get("model_score"),
                    "mean_threat_score": payload.get("mean_threat_score"),
                    "worst_case_threat_score": payload.get("worst_case_threat_score"),
                    "formula_version": payload.get("formula_version"),
                    "formula": payload.get("formula"),
                    "warnings": payload.get("warnings", []),
                },
                "selection": {
                    "status": "evidence_review_required",
                    "label": "More evidence required before model selection",
                    "reason": "This run records execution and detector-native observations only. It has no independent human outcome labels or validated safety decision rule.",
                },
                "interpretation": {
                    "observed_detector_signals": "Detector signals are observations, not confirmed successful attacks or ground-truth safety outcomes.",
                    "model_score": "The model score is an engineering detector summary, not a safety rating, ranking, or recommendation.",
                },
            }

    def register(name, entity):
        allowed = FILTERS.intersection(entity.__table__.columns.keys())

        def listing(limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0),
                    filter_by: str | None = None, value: str | None = None,
                    sort: str = "created_at", direction: str = "asc"):
            if sort not in {"id", "created_at"} or direction not in {"asc", "desc"}:
                raise HTTPException(422, "Invalid sort")
            if (filter_by is None) != (value is None) or (filter_by is not None and filter_by not in allowed):
                raise HTTPException(422, "Invalid filter")
            statement = select(entity)
            if filter_by is not None:
                statement = statement.where(getattr(entity, filter_by) == value)
            with factory() as session:
                total = session.scalar(select(func.count()).select_from(statement.subquery()))
                column = getattr(entity, sort)
                rows = session.scalars(statement.order_by(
                    column.desc() if direction == "desc" else column.asc(), entity.id).limit(limit).offset(offset))
                return {"items": [project(row) for row in rows], "total": total, "limit": limit, "offset": offset}

        def detail(record_id: str):
            with factory() as session:
                row = session.get(entity, record_id)
                if row is None:
                    raise HTTPException(404, "Record not found")
                return project(row)

        app.add_api_route(f"/{name}", listing, methods=["GET"], name=f"list_{name}")
        app.add_api_route(f"/{name}/{{record_id}}", detail, methods=["GET"], name=f"get_{name}")

    for name, entity in RESOURCES.items():
        register(name, entity)


def _model_score_status(stored_status: str | None, payload: dict[str, object]) -> str | None:
    """Ensure legacy detector summaries do not look like scientific results."""
    if str(payload.get("formula_version") or "").startswith("engineering-detector-"):
        return "engineering_only"
    return stored_status
