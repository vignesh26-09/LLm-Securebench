"""On-demand adapters to the existing metric engines.

These calculations are ephemeral. Caller-supplied measurements and calibration
artifacts are not independent validation evidence and are never persisted here.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
import re
from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from core.dataset.models import Dataset
from core.dataset.quality import DqiWeights, calculate_dqi
from core.draa.diagnostics import summarize as summarize_draa
from core.draa.models import DRAAEvidenceRecord
from core.metrics.bsda import BSDAInput, BSDACalibrationArtifact, BSDAValidationError
from core.metrics.bsda_adapters import (
    DetectorSafetyClassifier, LexicalSemanticRepresentation, compute_bsda_with_adapters,
)
from core.persistence.models import ScientificRecordEntity
from core.prediction.baselines import LogisticRegressionConfig
from core.prediction.models import FeatureRecord, FeatureSchema, PredictionTask, SplitManifest, TargetRecord
from core.prediction.training import train_fixture_baselines
from core.pri.diagnostics import summarize as summarize_pri
from core.pri.models import PRIProfileRecord
from core.recovery.engine import RecoveryCapabilityEngine
from core.recovery.models import RCCalibrationArtifact, RecoveryRunInput
from core.saea.engine import SAEAEngine
from core.saea.models import SAEAInput
from core.statistics.descriptive import summarize as summarize_statistics


METRIC_FAMILIES = {
    "bsda": ("bsda",),
    "recovery": ("rc", "recovery"),
    "saea": ("saea",),
    "draa": ("draa",),
    "pri": ("pri",),
    "dqi": ("dqi",),
    "ml": ("ml",),
    "statistics": ("statistics",),
}
REQUIRED_FIELDS = {
    "bsda": ("value",), "recovery": ("value",), "saea": ("value",),
    "draa": ("records",), "pri": ("profile",), "dqi": ("dataset",),
    "ml": ("experiment_id", "task", "schema", "features", "targets", "manifest", "logistic_config"),
    "statistics": ("values",),
}
LOCAL_RUN_PERSISTS = frozenset({"draa", "pri", "ml", "statistics"})
_SECRET_SHAPE = re.compile(r"SLB-[A-Z2-9]{20}")


def _public(value: Any) -> Any:
    """Exclude caller-supplied free-text provenance and redact trial secrets."""
    if isinstance(value, dict):
        return {key: _public(item) for key, item in value.items()
                if key not in {"metadata", "provenance", "generation_config"}}
    if isinstance(value, list):
        return [_public(item) for item in value]
    if isinstance(value, str):
        return _SECRET_SHAPE.sub("[REDACTED]", value)
    return value


def _parse(type_: Any, value: Any) -> Any:
    try:
        return TypeAdapter(type_).validate_python(value)
    except (ValidationError, ValueError, TypeError) as error:
        # Validation errors may embed supplied response text or a synthetic secret.
        raise HTTPException(422, f"invalid_{getattr(type_, '__name__', 'metric_input')}") from None


def _required(payload: dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise HTTPException(422, f"missing_{key}")
    return payload[key]


def _result(metric: str, value: Any, *, status: str | None = None) -> dict[str, Any]:
    source_status = getattr(value, "status", getattr(value, "computation_status", "computed"))
    return {
        "metric": metric,
        "status": status or str(source_status),
        "result": _public(jsonable_encoder(asdict(value))),
        "evidence_class": "ephemeral_supplied_input",
        "input_verification": "caller_supplied_unverified",
        "scientific_validation": "not_established",
        "persisted": False,
    }


def compute_metric(metric: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Run the unchanged source engine on explicitly supplied, typed inputs."""
    if metric not in METRIC_FAMILIES:
        raise HTTPException(404, "Metric not found")
    if metric == "bsda":
        value = _parse(BSDAInput, _required(payload, "value"))
        if value.n_runs > 1000:
            raise HTTPException(422, "too_many_bsda_pairs")
        adapter = payload.get("semantic_adapter", "lexical")
        if adapter not in {"lexical", "none"}:
            raise HTTPException(422, "unsupported_semantic_adapter")
        calibration = _parse(BSDACalibrationArtifact, payload["calibration"]) if payload.get("calibration") is not None else None
        try:
            result = compute_bsda_with_adapters(
                value, semantic=LexicalSemanticRepresentation() if adapter == "lexical" else None,
                safety=DetectorSafetyClassifier(), calibration=calibration,
                provenance={"semantic_adapter": adapter, "input_source": "caller_supplied"},
            )
        except (BSDAValidationError, ValueError):
            raise HTTPException(422, "invalid_bsda_measurement") from None
        return _result(metric, result, status="component_vector_computed")
    if metric == "recovery":
        value = _parse(RecoveryRunInput, _required(payload, "value"))
        if len(value.baseline_states) > 1000 or len(value.recovery_steps) > 1000:
            raise HTTPException(422, "too_many_recovery_states")
        calibration = _parse(RCCalibrationArtifact, payload["calibration"]) if payload.get("calibration") is not None else None
        return _result(metric, RecoveryCapabilityEngine().evaluate_run(value, calibration))
    if metric == "saea":
        value = _parse(SAEAInput, _required(payload, "value"))
        if len(value.attacks) > 100:
            raise HTTPException(422, "too_many_saea_steps")
        return _result(metric, SAEAEngine().evaluate(value))
    if metric == "draa":
        records = _parse(tuple[DRAAEvidenceRecord, ...], _required(payload, "records"))
        if not records or len(records) > 5000:
            raise HTTPException(422, "draa_records_required")
        diagnostics = summarize_draa(records)
        return _result(metric, diagnostics, status="descriptive_diagnostics_computed" if diagnostics.feature_count else "insufficient_data")
    if metric == "pri":
        profile = _parse(PRIProfileRecord, _required(payload, "profile"))
        if len(profile.cells) > 100000:
            raise HTTPException(422, "too_many_pri_cells")
        diagnostics = summarize_pri(profile)
        return _result(metric, diagnostics, status="descriptive_diagnostics_computed" if profile.cells else "insufficient_data")
    if metric == "dqi":
        dataset = _parse(Dataset, _required(payload, "dataset"))
        if len(dataset.records) > 10000:
            raise HTTPException(422, "too_many_dataset_records")
        embeddings = _parse(tuple[tuple[float, ...] | None, ...], payload["embeddings"]) if payload.get("embeddings") is not None else None
        if embeddings is not None and len(embeddings) != len(dataset.records):
            raise HTTPException(422, "embedding_record_count_mismatch")
        if embeddings is not None and len(embeddings) > 1000:
            raise HTTPException(422, "semantic_novelty_pairwise_limit")
        if embeddings is not None and any(vector is not None and
                (not vector or any(not math.isfinite(item) for item in vector)) for vector in embeddings):
            raise HTTPException(422, "invalid_semantic_embedding")
        dimensions = {len(vector) for vector in embeddings or () if vector is not None}
        if len(dimensions) > 1:
            raise HTTPException(422, "embedding_dimension_mismatch")
        weights = _parse(DqiWeights, payload["weights"]) if payload.get("weights") is not None else DqiWeights()
        try:
            result = calculate_dqi(dataset, embeddings=embeddings, weights=weights)
        except ValueError:
            raise HTTPException(422, "invalid_dqi_input") from None
        return _result(metric, result)
    if metric == "statistics":
        values = _parse(tuple[float, ...], _required(payload, "values"))
        if len(values) > 100000:
            raise HTTPException(422, "too_many_statistical_values")
        return _result(metric, summarize_statistics(values))
    task = _parse(PredictionTask, _required(payload, "task"))
    schema = _parse(FeatureSchema, _required(payload, "schema"))
    features = _parse(tuple[FeatureRecord, ...], _required(payload, "features"))
    targets = _parse(tuple[TargetRecord, ...], _required(payload, "targets"))
    manifest = _parse(SplitManifest, _required(payload, "manifest"))
    config = _parse(LogisticRegressionConfig, _required(payload, "logistic_config"))
    experiment_id = _parse(str, _required(payload, "experiment_id"))
    if len(features) > 100000 or len(targets) > 100000 or config.max_iterations > 1000:
        raise HTTPException(422, "ml_input_limit_exceeded")
    try:
        training = train_fixture_baselines(
            experiment_id=experiment_id, task=task, schema=schema, features=features,
            targets=targets, manifest=manifest, logistic_config=config,
        )
    except ValueError:
        raise HTTPException(422, "invalid_ml_input") from None
    # Return the model artifact and held-out metrics, never the raw labels or
    # a claim that a caller-supplied split has been independently audited.
    return {
        "metric": metric, "status": training.status, "reason": training.reason,
        "metrics": _public(jsonable_encoder(training.metrics)),
        "experiment": _public(jsonable_encoder(asdict(training.experiment))) if training.experiment else None,
        "evidence_class": "ephemeral_supplied_input", "input_verification": "caller_supplied_unverified",
        "scientific_validation": "not_established",
        "persisted": False,
    }


def register_metric_compute(app, factory) -> None:
    @app.get("/metrics/catalog")
    def metric_catalog():
        with factory() as session:
            rows = session.execute(select(
                ScientificRecordEntity.family, ScientificRecordEntity.status, func.count(),
            ).group_by(ScientificRecordEntity.family, ScientificRecordEntity.status)).all()
        counts = {metric: {"records": 0, "statuses": {}} for metric in METRIC_FAMILIES}
        for family, status, count in rows:
            for metric, families in METRIC_FAMILIES.items():
                if family in families:
                    counts[metric]["records"] += count
                    key = status or "unspecified"
                    counts[metric]["statuses"][key] = counts[metric]["statuses"].get(key, 0) + count
        return {"items": [
            {"metric": metric, "compute_path": f"/metrics/compute/{metric}", **counts[metric],
             "required_fields": REQUIRED_FIELDS[metric],
             "ordinary_run_persists_family": metric in LOCAL_RUN_PERSISTS,
             "scientific_validation": "not_established"}
            for metric in METRIC_FAMILIES
        ]}

    @app.post("/metrics/compute/{metric}")
    def compute(metric: str, payload: dict[str, Any]):
        return compute_metric(metric, payload)

    @app.post("/metrics/compute/{metric}/save", status_code=201)
    def compute_and_save(metric: str, payload: dict[str, Any]):
        """Append an engineering-only projection; never upgrade it to science."""
        calculated = compute_metric(metric, payload)
        try:
            canonical = json.dumps({"schema_version": "metric-api-v1", "metric": metric, "input": payload},
                                   sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError):
            raise HTTPException(422, "invalid_metric_input") from None
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record_id = f"metric-api:{metric}:{digest}"
        family = METRIC_FAMILIES[metric][0]
        source_result = calculated.get("result", {
            "status": calculated["status"], "reason": calculated.get("reason"),
            "metrics": calculated.get("metrics"), "experiment": calculated.get("experiment"),
        })
        record = ScientificRecordEntity(
            id=record_id, family=family, schema_version="metric-api-v1",
            scope="ENGINEERING_CALCULATION", owner_id=None,
            status=calculated["status"], payload=source_result,
            provenance={
                "reporting_class": "engineering_only",
                "data_origin": "caller_supplied_unverified",
                "scientifically_validated": False,
                "source": "apps.api.metric_compute",
                "input_sha256": digest,
            },
        )
        try:
            with factory() as session, session.begin():
                if session.get(ScientificRecordEntity, record_id) is not None:
                    raise HTTPException(409, "Immutable metric calculation already exists")
                session.add(record)
        except IntegrityError:
            raise HTTPException(409, "Immutable metric calculation already exists") from None
        return {**calculated, "record_id": record_id, "persisted": True,
                "evidence_class": "engineering_only"}
