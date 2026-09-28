"""Immutable preregistration and analysis-lock artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Mapping, Sequence

from core.experiments.manifest import stable_hash
from core.experiments.models import utc_now


class PreregistrationStatus(StrEnum):
    DRAFT = "draft"
    LOCKED = "locked"
    AMENDED = "amended"


@dataclass(frozen=True, slots=True)
class Preregistration:
    preregistration_id: str
    experiment_id: str
    version: int
    research_questions: tuple[str, ...]
    planned_tests: tuple[str, ...]
    planned_metrics: tuple[str, ...]
    complementarity_procedure: str
    status: PreregistrationStatus
    created_at: str
    locked_at: str | None
    parent_preregistration_id: str | None = None
    amendment_reason: str | None = None
    content_hash: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.preregistration_id or not self.experiment_id or self.version <= 0:
            raise ValueError("preregistration identity and positive version are required")
        if self.status is PreregistrationStatus.LOCKED and not self.locked_at:
            raise ValueError("locked preregistrations require a lock timestamp")


@dataclass(frozen=True, slots=True)
class AnalysisPlanDiff:
    preregistration_id: str
    analysis_id: str
    status: str
    planned_items: tuple[str, ...]
    requested_items: tuple[str, ...]
    unplanned_items: tuple[str, ...]
    created_at: str


def lock_preregistration(*, preregistration_id: str, experiment_id: str,
                         research_questions: Sequence[str], planned_tests: Sequence[str],
                         planned_metrics: Sequence[str], complementarity_procedure: str,
                         metadata: Mapping[str, object] | None = None) -> Preregistration:
    created = utc_now()
    content = {"experiment_id": experiment_id, "research_questions": tuple(research_questions),
               "planned_tests": tuple(planned_tests), "planned_metrics": tuple(planned_metrics),
               "complementarity_procedure": complementarity_procedure, "metadata": dict(metadata or {})}
    return Preregistration(preregistration_id, experiment_id, 1, tuple(research_questions),
                            tuple(planned_tests), tuple(planned_metrics), complementarity_procedure,
                            PreregistrationStatus.LOCKED, created, created,
                            content_hash=stable_hash(content), metadata=dict(metadata or {}))


def amend_preregistration(prior: Preregistration, *, preregistration_id: str,
                          amendment_reason: str, research_questions: Sequence[str] | None = None,
                          planned_tests: Sequence[str] | None = None,
                          planned_metrics: Sequence[str] | None = None,
                          complementarity_procedure: str | None = None) -> Preregistration:
    if prior.status not in {PreregistrationStatus.LOCKED, PreregistrationStatus.AMENDED}:
        raise ValueError("only a locked preregistration can be amended")
    if not amendment_reason:
        raise ValueError("an amendment reason is required")
    draft = replace(prior, preregistration_id=preregistration_id, version=prior.version + 1,
                    research_questions=tuple(research_questions or prior.research_questions),
                    planned_tests=tuple(planned_tests or prior.planned_tests),
                    planned_metrics=tuple(planned_metrics or prior.planned_metrics),
                    complementarity_procedure=complementarity_procedure or prior.complementarity_procedure,
                    status=PreregistrationStatus.AMENDED, created_at=utc_now(), locked_at=utc_now(),
                    parent_preregistration_id=prior.preregistration_id, amendment_reason=amendment_reason,
                    content_hash="")
    return replace(draft, content_hash=stable_hash({"parent": prior.content_hash, "version": draft.version,
                                                    "questions": draft.research_questions, "tests": draft.planned_tests,
                                                    "metrics": draft.planned_metrics, "procedure": draft.complementarity_procedure,
                                                    "reason": amendment_reason}))


def compare_analysis_plan(preregistration: Preregistration, *, analysis_id: str,
                          requested_items: Sequence[str]) -> AnalysisPlanDiff:
    planned = tuple(preregistration.planned_tests + preregistration.planned_metrics +
                    (preregistration.complementarity_procedure,))
    requested = tuple(requested_items)
    unplanned = tuple(item for item in requested if item not in planned)
    return AnalysisPlanDiff(preregistration.preregistration_id, analysis_id,
                            "as_planned" if not unplanned else "exploratory_not_preregistered",
                            planned, requested, unplanned, utc_now())
