from dataclasses import replace

import pytest

from core.experiments.models import ControlMatchIdentity
from core.saea.engine import SAEAEngine
from core.saea.models import (
    AttackInstance, BehavioralState, ContextStatus, ResultStatus, SAEAInput,
    SpacingCondition,
)


def verified_input():
    identity = ControlMatchIdentity(
        evaluation_case_id="synthetic-case", attack_id="synthetic-attack",
        attack_instance_id="synthetic-instance", target_model="synthetic-model",
        target_model_version="v1", provider="synthetic", generation_digest="fixed",
        dataset_version="v1", behavior_representation_version="v1",
        layer1_version="v1", layer2_judge_version="v1",
        measurement_version="v1", threat_model="synthetic",
    )
    attack = AttackInstance(
        attack_instance_id="synthetic-instance", attack_id="synthetic-attack",
        category="synthetic", technique_family="synthetic", position=1,
        evaluation_case_id="synthetic-case",
        state=BehavioralState("sequential", {"safety": 0.6, "helpfulness": 0.6}),
        isolated_state=BehavioralState("isolated", {"safety": 0.2, "helpfulness": 0.2}),
        isolated_baseline=(BehavioralState("isolated-baseline", {"safety": 0.0, "helpfulness": 0.0}),),
        sequential_identity=identity, isolated_identity=identity,
        contamination_status="isolation_verified",
    )
    return SAEAInput(
        "synthetic-run", "synthetic-sequence", "synthetic-model", "synthetic", "v1",
        (BehavioralState("baseline", {"safety": 0.0, "helpfulness": 0.0}),), (attack,),
        SpacingCondition.STACKED, ContextStatus.RETAINED,
    )


def assert_unavailable(result, reason):
    assert result.status is ResultStatus.UNDEFINED
    assert result.reason == "isolated_control_unavailable"
    step = result.per_step[0]
    assert step.status is ResultStatus.UNDEFINED
    assert step.reason == reason
    assert step.isolated_delta is None
    assert step.context_effect is None
    assert result.synergy.status is ResultStatus.UNDEFINED
    assert result.synergy.bliss_expected_effect is None
    assert result.synergy.synergy_index is None


def test_both_control_identities_missing_blocks_context_effect():
    value = verified_input()
    attack = replace(value.attacks[0], sequential_identity=None, isolated_identity=None)
    result = SAEAEngine().evaluate(replace(value, attacks=(attack,)))
    assert_unavailable(result, "missing_control_match_identity")


@pytest.mark.parametrize("status", ["isolation_unverifiable", "isolation_cannot_be_determined", None])
def test_isolation_without_verification_blocks_context_effect(status):
    value = verified_input()
    attack = replace(value.attacks[0], contamination_status=status)
    result = SAEAEngine().evaluate(replace(value, attacks=(attack,)))
    assert_unavailable(result, "control_isolation_not_verified")


def test_verified_isolation_and_matching_identities_preserve_computation():
    result = SAEAEngine().evaluate(verified_input())
    assert result.status is ResultStatus.APPLICABLE
    step = result.per_step[0]
    assert step.status is ResultStatus.APPLICABLE
    assert step.reason is None
    assert step.isolated_delta == pytest.approx(0.2)
    assert step.context_effect == pytest.approx(0.4)
    assert result.synergy.synergy_index == pytest.approx(3.0)
