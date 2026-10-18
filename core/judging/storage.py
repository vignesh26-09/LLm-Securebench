"""Machine-readable JSON storage for individual Layer 2 judge measurements."""

import json
from dataclasses import asdict
from pathlib import Path

from core.judging.models import JudgeDimension, JudgeLabel, JudgeResult, JudgmentStatus


class JsonJudgeResultStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def save(self, result: JudgeResult) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{result.evaluation_id}-{result.dimension.value}.json"
        path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def load(self, evaluation_id: str, dimension: JudgeDimension) -> JudgeResult | None:
        path = self._directory / f"{evaluation_id}-{dimension.value}.json"
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        value["dimension"] = JudgeDimension(value["dimension"])
        value["status"] = JudgmentStatus(value["status"])
        if value["label"] is not None:
            value["label"] = JudgeLabel(value["label"])
        value["evidence_citations"] = tuple(value["evidence_citations"])
        return JudgeResult(**value)
