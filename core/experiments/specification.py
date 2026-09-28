"""Strict JSON loading for versioned experiment specifications."""

from __future__ import annotations

import json
from pathlib import Path

from core.experiments.models import (AttackDefinition, EvaluationCaseDesign,
    ExperimentSpecification, MeasurementConfiguration)
from core.inference.contracts import GenerationConfig
from core.models.registry import ModelMetadata


def load_experiment_specification(path: Path) -> ExperimentSpecification:
    value = json.loads(path.read_text(encoding="utf-8"))
    models = tuple(ModelMetadata(
        item["name"], item["provider"], item.get("version"), item.get("context_window"),
        frozenset(item.get("capabilities", ())), item.get("metadata", {}))
        for item in value["models"])
    cases = tuple(EvaluationCaseDesign(
        item["evaluation_case_id"], item["baseline_prompt"],
        tuple(AttackDefinition(**attack) for attack in item["attacks"]),
        tuple(tuple(sequence) for sequence in item.get("sequences", ())),
        tuple(item.get("recovery_probes", ()))) for item in value["cases"])
    return ExperimentSpecification(
        experiment_id=value["experiment_id"], dataset_id=value["dataset_id"],
        dataset_version=value["dataset_version"], dataset_hash=value["dataset_hash"],
        models=models, cases=cases, generation=GenerationConfig(**value.get("generation", {})),
        seeds=tuple(value["seeds"]), repetitions=int(value["repetitions"]),
        measurement=MeasurementConfiguration(**value["measurement"]),
        system_prompt=value.get("system_prompt"),
        specification_version=value.get("specification_version", "controlled-trajectory-v1"),
        preregistration_id=value.get("preregistration_id"),
        canary_policy=value.get("canary_policy", {}), metadata=value.get("metadata", {}))
