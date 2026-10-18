"""Claim-specific evaluator eligibility; no universal accuracy threshold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class EvaluatorEligibilityPolicy:
    claim_id: str
    locked_policy_artifact_id: str
    locked_before_evaluation: bool
    minimum_coverage: float
    maximum_false_positive_rate: float
    maximum_false_negative_rate: float

    def __post_init__(self):
        if not self.claim_id or not self.locked_policy_artifact_id:
            raise ValueError("claim and locked policy artifact identity required")
        for value in (self.minimum_coverage, self.maximum_false_positive_rate,
                      self.maximum_false_negative_rate):
            if not 0 <= value <= 1:
                raise ValueError("eligibility bounds must be in [0,1]")


def assess_evaluator_eligibility(comparison: Mapping[str, object], *, evaluator_name: str,
                                 policy: EvaluatorEligibilityPolicy | None,
                                 independent_human_reference: bool) -> dict[str, object]:
    """Use upper clustered interval bounds for errors on an actual held-out set.

    A policy identity/lock flag is evidence supplied by the caller. The caller
    must separately verify that artifact's timestamp and immutability.
    """
    if policy is None:
        return {"status": "not_assessed", "reason": "claim_specific_locked_policy_required"}
    if not policy.locked_before_evaluation:
        return {"status": "blocked", "reason": "policy_not_locked_before_evaluation"}
    if comparison.get("status") != "held_out_test":
        return {"status": "blocked", "reason": "held_out_test_evidence_required"}
    if not independent_human_reference:
        return {"status": "blocked", "reason": "independent_human_reference_required"}
    evaluators = comparison.get("evaluators", {})
    if evaluator_name not in evaluators:
        raise ValueError("unknown evaluator")
    record = evaluators[evaluator_name]
    stats = record["common_case"]
    intervals = stats.get("cluster_bootstrap_intervals")
    if not intervals or intervals.get("false_positive_rate") is None or intervals.get("false_negative_rate") is None:
        return {"status": "blocked", "reason": "grouped_error_intervals_required"}
    observed = {"coverage": record["source_coverage"],
                "false_positive_rate_upper": intervals["false_positive_rate"][1],
                "false_negative_rate_upper": intervals["false_negative_rate"][1]}
    violations = []
    if observed["coverage"] < policy.minimum_coverage:
        violations.append("coverage_below_claim_policy")
    if observed["false_positive_rate_upper"] > policy.maximum_false_positive_rate:
        violations.append("false_positive_uncertainty_exceeds_claim_policy")
    if observed["false_negative_rate_upper"] > policy.maximum_false_negative_rate:
        violations.append("false_negative_uncertainty_exceeds_claim_policy")
    return {"status": "eligible_for_claim_review" if not violations else "ineligible_for_claim",
            "claim_id": policy.claim_id, "policy_artifact_id": policy.locked_policy_artifact_id,
            "observed": observed, "violations": violations,
            "notice": "Eligibility is claim-specific and still requires scientific review; it is not a universal safety certification."}
