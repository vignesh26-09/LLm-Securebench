"""Versioned goal records; selection is independent of defender outcomes."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import re


class GoalSplit(StrEnum):
    DEVELOPMENT = "development"
    PILOT = "pilot"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class GoalCase:
    goal_id: str
    split: GoalSplit
    source_uri: str
    source_revision: str
    source_sha256: str
    goal_content_sha256: str
    source_license: str
    objective: str
    legitimate_task_id: str
    topic_id: str
    probe_family_id: str
    attack_script_id: str
    benign_script_id: str
    duplicate_review_id: str
    version: int = 1
    schema_version: str = "feasibility-goal-v1"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", self.goal_id):
            raise ValueError("Invalid goal identity")
        if (not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256)
                or not re.fullmatch(r"[0-9a-f]{64}", self.goal_content_sha256)):
            raise ValueError("Source and goal-content SHA-256 required")
        if self.version < 1 or any(not getattr(self, field) for field in (
            "source_uri", "source_revision", "source_license", "objective",
            "legitimate_task_id", "topic_id", "probe_family_id", "attack_script_id",
            "benign_script_id", "duplicate_review_id")):
            raise ValueError("Incomplete goal provenance")

    @property
    def content_sha256(self) -> str:
        from dataclasses import asdict
        return digest(asdict(self))


def validate_goal_sets(development: tuple[GoalCase, ...], pilot: tuple[GoalCase, ...]) -> None:
    """Reject identity/source overlap; semantic duplicates still need human review."""
    if any(case.split != GoalSplit.DEVELOPMENT for case in development) or any(
        case.split != GoalSplit.PILOT for case in pilot
    ):
        raise ValueError("Goal split mismatch")
    all_cases = development + pilot
    if len({case.goal_id for case in all_cases}) != len(all_cases):
        raise ValueError("Duplicate goal identity across splits")
    if len({case.goal_content_sha256 for case in all_cases}) != len(all_cases):
        raise ValueError("Duplicate goal content across splits")

