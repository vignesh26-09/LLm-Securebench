"""Safe import of the existing, checksummed calibration artifact into SQLite."""

from __future__ import annotations

import json
from pathlib import Path

from core.persistence.models import ScientificRecordEntity


CALIBRATION_ARTIFACT_ID = "jbb-gemma-fixed-mapping-v1"


def import_persisted_judge_calibration(session, path: Path) -> bool:
    """Import only the repository's real calibration artifact, once.

    The source JSON remains authoritative; this merely creates a queryable
    database projection and records its exact source path/checksum metadata.
    """
    existing = session.get(ScientificRecordEntity, CALIBRATION_ARTIFACT_ID)
    if existing is not None:
        if existing.family != "judge_calibration":
            raise ValueError("conflicting_calibration_artifact_identifier")
        if (existing.provenance or {}).get("reporting_class") == "external_calibration":
            return False
        existing.provenance = {**dict(existing.provenance or {}), "data_origin": "real_persisted",
                               "fixture": False, "synthetic": False,
                               "reporting_class": "external_calibration"}
        session.commit()
        return True
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("artifact_id") != CALIBRATION_ARTIFACT_ID or payload.get("sample_size") != 300:
        raise ValueError("unexpected_judge_calibration_artifact")
    source_provenance = dict(payload.get("provenance", {}))
    session.add(ScientificRecordEntity(
        id=CALIBRATION_ARTIFACT_ID, family="judge_calibration", schema_version="judge-calibration-v1",
        scope="CALIBRATION", owner_id=payload.get("dataset"), status=payload.get("validation_status"),
        payload=payload, provenance={**source_provenance, "data_origin": "real_persisted", "fixture": False,
                                     "synthetic": False, "reporting_class": "external_calibration",
                                     "source_artifact": str(path),
                                     "dataset_hash": payload.get("dataset_hash"),
                                     "dataset_revision": payload.get("dataset_revision")},
    ))
    session.commit()
    return True
