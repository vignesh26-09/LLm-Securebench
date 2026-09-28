"""Self-contained export and factual replay comparison for controlled runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Mapping, Sequence

from core.experiments.manifest import stable_hash
from core.experiments.models import utc_now


@dataclass(frozen=True, slots=True)
class ReplicationBundle:
    bundle_id: str
    schema_version: str
    created_at: str
    experiment_specification: Mapping[str, object]
    observations: tuple[Mapping[str, object], ...]
    manifest: Mapping[str, object] | None
    preregistrations: tuple[Mapping[str, object], ...]
    contamination_ledger: tuple[Mapping[str, object], ...]
    layer1_signals: Mapping[str, object]
    layer2_signals: Mapping[str, object]
    content_hash: str


@dataclass(frozen=True, slots=True)
class ReplayDifference:
    observation_id: str
    response_status: str
    layer1_status: str
    layer2_status: str
    context_status: str
    original_response: str | None
    replay_response: str | None
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReplayReport:
    bundle_id: str
    replay_id: str
    created_at: str
    differences: tuple[ReplayDifference, ...]
    status: str


def export_bundle(*, bundle_id: str, specification: object, observations: Sequence[object],
                  manifest: object | None = None, preregistrations: Sequence[object] = (),
                  contamination_ledger: Sequence[object] = (),
                  layer1_signals: Mapping[str, object] | None = None,
                  layer2_signals: Mapping[str, object] | None = None) -> ReplicationBundle:
    payload = {"specification": _value(specification), "observations": [_value(item) for item in observations],
               "manifest": _value(manifest) if manifest else None,
               "preregistrations": [_value(item) for item in preregistrations],
               "contamination_ledger": [_value(item) for item in contamination_ledger],
               "layer1_signals": _value(layer1_signals or {}), "layer2_signals": _value(layer2_signals or {})}
    return ReplicationBundle(bundle_id, "replication-bundle-v1", utc_now(), payload["specification"],
                             tuple(payload["observations"]), payload["manifest"], tuple(payload["preregistrations"]),
                             tuple(payload["contamination_ledger"]), payload["layer1_signals"], payload["layer2_signals"],
                             stable_hash(payload))


def write_bundle(bundle: ReplicationBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_value(bundle), indent=2, sort_keys=True), encoding="utf-8")


def load_bundle(path: Path) -> ReplicationBundle:
    value = json.loads(path.read_text(encoding="utf-8"))
    return ReplicationBundle(**value)


def compare_replay(bundle: ReplicationBundle, replay_observations: Sequence[object], *, replay_id: str,
                   replay_layer1_signals: Mapping[str, object] | None = None,
                   replay_layer2_signals: Mapping[str, object] | None = None) -> ReplayReport:
    replay = {_value(item)["observation_id"]: _value(item) for item in replay_observations}
    layer1 = replay_layer1_signals or {}
    layer2 = replay_layer2_signals or {}
    rows = []
    for original in bundle.observations:
        observation_id = str(original["observation_id"])
        current = replay.get(observation_id)
        response_status = "missing_replay_observation" if current is None else (
            "identical" if current.get("response") == original.get("response") else "different")
        context_status = "missing_replay_observation" if current is None else (
            "identical" if current.get("context_status") == original.get("context_status") else "different")
        rows.append(ReplayDifference(
            observation_id, response_status,
            _signal_diff(bundle.layer1_signals.get(observation_id), layer1.get(observation_id)),
            _signal_diff(bundle.layer2_signals.get(observation_id), layer2.get(observation_id)),
            context_status, original.get("response"), current.get("response") if current else None,
            {"original_canary": original.get("canary_evidence"),
             "replay_canary": current.get("canary_evidence") if current else None}))
    status = "identical" if rows and all(row.response_status == "identical" and row.context_status == "identical"
                                         for row in rows) else "differences_observed"
    return ReplayReport(bundle.bundle_id, replay_id, utc_now(), tuple(rows), status)


def _signal_diff(original: object, replay: object) -> str:
    if original is None:
        return "not_exported"
    if replay is None:
        return "replay_signal_unavailable"
    return "identical" if original == replay else "different"


def _value(value: object) -> object:
    if is_dataclass(value):
        return _value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_value(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value
