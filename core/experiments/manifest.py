"""Reproducibility manifests and stable artifact hashes."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from dataclasses import dataclass, field
from typing import Mapping, Sequence


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ReproducibilityManifest:
    experiment_id: str
    git_commit: str | None
    dirty_working_tree: bool | None
    dataset_identity: Mapping[str, object]
    models: tuple[Mapping[str, object], ...]
    provider: str
    generation_settings: Mapping[str, object]
    requested_seeds: tuple[int, ...]
    effective_seeds: tuple[int | None, ...]
    provider_supports_seed: bool | None
    judge_identity: Mapping[str, object] | None
    rubric_prompt_versions: Mapping[str, object]
    detector_configuration: Mapping[str, object]
    metric_versions: Mapping[str, str]
    software_versions: Mapping[str, str | None]
    python_version: str
    platform: str
    experiment_start: str
    experiment_end: str
    case_count: int
    condition_count: int
    successful_count: int
    failed_count: int
    artifact_hashes: Mapping[str, str]
    unavailable_reasons: Mapping[str, str] = field(default_factory=dict)


def git_state(root: str) -> tuple[str | None, bool | None, str | None]:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout.strip())
        return commit, dirty, None
    except (OSError, subprocess.CalledProcessError) as error:
        return None, None, str(error)


def runtime_versions() -> Mapping[str, str | None]:
    try:
        import sqlalchemy
        sqlalchemy_version = sqlalchemy.__version__
    except ImportError:
        sqlalchemy_version = None
    try:
        import fastapi
        fastapi_version = fastapi.__version__
    except ImportError:
        fastapi_version = None
    return {"securellmbench": "0.1.0", "sqlalchemy": sqlalchemy_version, "fastapi": fastapi_version}


def build_manifest(spec, observations: Sequence[object], *, root: str,
                   experiment_start: str, experiment_end: str,
                   judge_identity: Mapping[str, object] | None = None,
                   artifact_hashes: Mapping[str, str] | None = None) -> ReproducibilityManifest:
    commit, dirty, git_reason = git_state(root)
    successful = sum(getattr(item, "status", None).value == "completed" for item in observations)
    failed = len(observations) - successful
    effective = tuple(dict.fromkeys(getattr(item, "effective_seed", None) for item in observations))
    seed_support = {getattr(item, "provider_supports_seed", None) for item in observations}
    unavailable = {}
    if git_reason:
        unavailable["git_state"] = git_reason
    if any(model.version is None for model in spec.models):
        unavailable["model_version"] = "one_or_more_model_versions_not_supplied"
    if judge_identity is None:
        unavailable["judge_identity"] = "judge_not_configured_for_execution_stage"
    return ReproducibilityManifest(
        spec.experiment_id, commit, dirty,
        {"id": spec.dataset_id, "version": spec.dataset_version, "hash": spec.dataset_hash},
        tuple({"name": model.name, "provider": model.provider, "version": model.version,
               "context_window": model.context_window} for model in spec.models),
        ",".join(sorted({model.provider for model in spec.models})), asdict(spec.generation),
        spec.seeds, effective, next(iter(seed_support)) if len(seed_support) == 1 else None,
        dict(judge_identity) if judge_identity else None,
        {"prompt": spec.measurement.prompt_version, "rubric": spec.measurement.rubric_version},
        {"layer1": {"version": spec.measurement.layer1_version,
                    "configuration": dict(spec.measurement.layer1_configuration)},
         "behavior_representation": spec.measurement.behavior_representation_version,
         "layer2_judge": {"version": spec.measurement.layer2_judge_version,
                          "configuration": dict(spec.measurement.layer2_judge_configuration)}},
        {"measurement": spec.measurement.measurement_version,
         "experiment_specification": spec.specification_version},
        runtime_versions(), sys.version, platform.platform(), experiment_start, experiment_end,
        len(spec.cases), len(observations), successful, failed,
        dict(artifact_hashes or {}), unavailable)
