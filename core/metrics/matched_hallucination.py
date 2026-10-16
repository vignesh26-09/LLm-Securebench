"""Descriptive paired factual-error contrast; no model or judge calls.

This is a proposed measurement, not a validated hallucination predictor.  The
caller must supply independently established factual labels and matched trials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Outcome = Literal["hallucinated", "verified_no_hallucination", "ambiguous", "unavailable"]
Context = Literal["retained_verified", "truncated_known", "retention_unverifiable"]
LabelSource = Literal["independent_human_agreement", "human_adjudicated"]


class FactualObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(min_length=1)
    arm: Literal["adversarial", "topic_matched_benign"]
    model_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    reference_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    configuration_id: str = Field(min_length=1)
    context_status: Context
    outcome: Outcome
    label_id: str | None = None
    label_source: LabelSource | None = None

    @model_validator(mode="after")
    def require_human_label_for_binary_outcome(self):
        if self.outcome in {"hallucinated", "verified_no_hallucination"}:
            if not self.label_id or self.label_source is None:
                raise ValueError("binary factual outcome requires an independent human label reference")
        elif self.label_id is not None or self.label_source is not None:
            raise ValueError("ambiguous or unavailable outcomes cannot carry a binary label reference")
        return self


class MatchedFactualPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pair_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    reference_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    configuration_id: str = Field(min_length=1)
    adversarial: FactualObservation | None = None
    topic_matched_benign: FactualObservation | None = None

    @model_validator(mode="after")
    def validate_pair(self):
        for arm, observation in (("adversarial", self.adversarial),
                                 ("topic_matched_benign", self.topic_matched_benign)):
            if observation is None:
                continue
            if observation.arm != arm or any((
                observation.model_id != self.model_id,
                observation.question_id != self.question_id,
                observation.reference_sha256 != self.reference_sha256,
                observation.configuration_id != self.configuration_id,
            )):
                raise ValueError("factual pair arms must share model, question, reference and configuration")
        if (self.adversarial is not None and self.topic_matched_benign is not None
                and self.adversarial.observation_id == self.topic_matched_benign.observation_id):
            raise ValueError("paired arms cannot share an observation")
        return self


@dataclass(frozen=True)
class MatchedHallucinationResult:
    methodology_version: str
    status: str
    reason: str | None
    assigned_pairs: int
    complete_context_valid_pairs: int
    incomplete_pairs: int
    adversarial_labeled_eligible: int
    benign_labeled_eligible: int
    adversarial_hallucinations_complete: int
    benign_hallucinations_complete: int
    adversarial_rate_complete: float | None
    benign_rate_complete: float | None
    complete_pair_lift: float | None
    assigned_population_lower_bound: float | None
    assigned_population_upper_bound: float | None
    context_invalid_observations: int
    ambiguous_or_unavailable_observations: int


def _eligible_value(observation: FactualObservation | None) -> int | None:
    if observation is None or observation.context_status != "retained_verified":
        return None
    if observation.outcome == "hallucinated":
        return 1
    if observation.outcome == "verified_no_hallucination":
        return 0
    return None


def compute_matched_hallucination_lift(pairs: tuple[MatchedFactualPair, ...]) -> MatchedHallucinationResult:
    """Mean paired A−T error difference and worst-case all-assigned bounds.

    The complete-pair estimate is descriptive; it is not an unrestricted ITT
    causal estimate.  Unknown binary outcomes are bounded, never coded as zero.
    """
    pair_ids = [pair.pair_id for pair in pairs]
    observation_ids = [observation.observation_id for pair in pairs
                       for observation in (pair.adversarial, pair.topic_matched_benign)
                       if observation is not None]
    if len(pair_ids) != len(set(pair_ids)) or len(observation_ids) != len(set(observation_ids)):
        raise ValueError("duplicate pair or observation identity")
    complete = a_positive = b_positive = a_eligible = b_eligible = 0
    lower_sum = upper_sum = context_invalid = other_unavailable = 0
    for pair in pairs:
        a = _eligible_value(pair.adversarial)
        b = _eligible_value(pair.topic_matched_benign)
        a_eligible += a is not None
        b_eligible += b is not None
        for observation in (pair.adversarial, pair.topic_matched_benign):
            if observation is not None and observation.context_status != "retained_verified":
                context_invalid += 1
            elif observation is not None and observation.outcome in {"ambiguous", "unavailable"}:
                other_unavailable += 1
        if a is not None and b is not None:
            complete += 1
            a_positive += a
            b_positive += b
        # Each missing arm ranges independently over {0, 1}.  Known one-arm
        # labels tighten the bounds without selecting only convenient pairs.
        lower_sum += (a if a is not None else 0) - (b if b is not None else 1)
        upper_sum += (a if a is not None else 1) - (b if b is not None else 0)
    n = len(pairs)
    return MatchedHallucinationResult(
        "matched-hallucination-lift-v1", "descriptive_unvalidated" if complete else "insufficient_data",
        None if complete else "no_complete_context_valid_human_labeled_pairs",
        n, complete, n - complete, a_eligible, b_eligible, a_positive, b_positive,
        a_positive / complete if complete else None,
        b_positive / complete if complete else None,
        (a_positive - b_positive) / complete if complete else None,
        lower_sum / n if n else None, upper_sum / n if n else None,
        context_invalid, other_unavailable,
    )
