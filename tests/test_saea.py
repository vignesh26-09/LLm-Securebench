"""Deterministic safe synthetic tests for reconciled SAEA calculations."""

import tempfile
import unittest
from pathlib import Path

from core.experiments.contamination import IsolationStatus, assess_isolation
from core.experiments.runner import ExperimentRunner, ObservationStore
from core.experiments.trajectory import BehaviorMeasurement, build_saea_input
from core.inference.mock import MockInferenceProvider
from core.saea import SAEAEngine, SAEAInput
from core.saea.models import (
    AttackInstance, BehavioralState, CoalitionEvaluation, ContextStatus,
    RecoveryWindow, ResultStatus, SAEAConfig, SpacingCondition,
)
from core.saea.statistics import bootstrap_synergy
from tests.test_research_protocol import specification


def state(identifier: str, safety: float, helpfulness: float, *, status: ResultStatus = ResultStatus.APPLICABLE) -> BehavioralState:
    return BehavioralState(identifier, {"safety": safety, "helpfulness": helpfulness}, status)


def attack(identifier: str, position: int, value: BehavioralState, isolated: BehavioralState | None = None, recovery: RecoveryWindow | None = None) -> AttackInstance:
    return AttackInstance(identifier, identifier.split("-")[0], "synthetic", "safe-test", position, "case", value, isolated or state(f"iso-{identifier}", 0.0, 0.0), (state(f"iso-base-{identifier}", 0.0, 0.0),), recovery_window=recovery)


def input_for(attacks: tuple[AttackInstance, ...], **kwargs: object) -> SAEAInput:
    return SAEAInput("run", "sequence", "mock", "synthetic", "v1", (state("base", 0.0, 0.0),), attacks, kwargs.get("spacing", SpacingCondition.STACKED), kwargs.get("context", ContextStatus.RETAINED), kwargs.get("config", SAEAConfig()), kwargs.get("coalitions", ()))


class SAEATest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SAEAEngine()

    def test_two_attack_bliss_and_per_step(self) -> None:
        first = attack("a-1", 1, state("a", 0.6, 0.0), state("ia", 0.2, 0.0))
        second = attack("b-1", 2, state("b", 0.0, 0.8), state("ib", 0.0, 0.4))
        result = self.engine.evaluate(input_for((first, second)))
        self.assertEqual(result.status, ResultStatus.APPLICABLE)
        self.assertAlmostEqual(result.trajectory.cumulative_vulnerability, (0.6 / 2**0.5 + 0.8 / 2**0.5) / 2)
        self.assertAlmostEqual(result.synergy.bliss_expected_effect, 1 - (1 - 0.2 / 2**0.5) * (1 - 0.4 / 2**0.5))
        self.assertAlmostEqual(result.per_step[0].context_effect, (0.6 - 0.2) / 2**0.5)

    def test_single_and_repeated_attacks(self) -> None:
        one = attack("repeat-1", 1, state("r1", 0.4, 0.4), state("ir1", 0.2, 0.2))
        two = attack("repeat-2", 2, state("r2", 0.6, 0.6), state("ir2", 0.1, 0.1))
        result = self.engine.evaluate(input_for((one, two)))
        self.assertEqual(result.order_effect.attack_order, ("repeat", "repeat"))
        self.assertEqual(len(result.per_step), 2)

    def test_missing_isolated_control_is_not_zero(self) -> None:
        value = attack("a-1", 1, state("a", 0.5, 0.5), state("ia", 0.2, 0.2))
        value = AttackInstance(value.attack_instance_id, value.attack_id, value.category, value.technique_family, value.position, value.evaluation_case_id, value.state, None)
        result = self.engine.evaluate(input_for((value,)))
        self.assertIsNone(result.per_step[0].isolated_delta)
        self.assertEqual(result.synergy.status, ResultStatus.UNDEFINED)

    def test_zero_denominator_is_not_applicable(self) -> None:
        item = attack("a-1", 1, state("a", 0.6, 0.6), state("ia", 0.0, 0.0))
        result = self.engine.evaluate(input_for((item,)))
        self.assertIsNone(result.synergy.synergy_index)
        self.assertEqual(result.synergy.status, ResultStatus.NOT_APPLICABLE)

    def test_context_truncation_and_failed_evaluation(self) -> None:
        item = attack("a-1", 1, state("a", 0.2, 0.2), state("ia", 0.1, 0.1))
        self.assertEqual(self.engine.evaluate(input_for((item,), context=ContextStatus.TRUNCATED)).reason, "context_window_validity_not_established")
        failed = attack("b-1", 1, state("failed", 0.2, 0.2, status=ResultStatus.FAILED_EVALUATION))
        self.assertEqual(self.engine.evaluate(input_for((failed,))).status, ResultStatus.FAILED_EVALUATION)

    def test_empty_baseline_and_missing_recovery_are_explicit(self) -> None:
        item = attack("a-1", 1, state("a", 0.2, 0.2), state("ia", 0.1, 0.1))
        empty = SAEAInput("run", "empty", "mock", "synthetic", "v1", (), (), SpacingCondition.STACKED, ContextStatus.RETAINED)
        self.assertEqual(self.engine.evaluate(empty).reason, "empty_sequence")
        no_baseline = SAEAInput("run", "no-base", "mock", "synthetic", "v1", (), (item,), SpacingCondition.STACKED, ContextStatus.RETAINED)
        self.assertEqual(self.engine.evaluate(no_baseline).reason, "missing_baseline")
        spaced = self.engine.evaluate(input_for((item,), spacing=SpacingCondition.SPACED))
        self.assertEqual(spaced.recovery_trend.status, ResultStatus.INSUFFICIENT_DATA)

    def test_recovery_and_shapley(self) -> None:
        gaps = tuple(RecoveryWindow(i, float(4 - i), ResultStatus.APPLICABLE) for i in range(1, 4))
        attacks = tuple(attack(f"a-{i}", i, state(f"s{i}", 0.2, 0.2), state(f"is{i}", 0.1, 0.1), gaps[i - 1] if i < 4 else None) for i in range(1, 5))
        preliminary = self.engine.evaluate(input_for(attacks, spacing=SpacingCondition.SPACED))
        ids = tuple(item.attack_instance_id for item in attacks)
        coalitions = (
            CoalitionEvaluation(frozenset(), 0.0),
            CoalitionEvaluation(frozenset({ids[0]}), 0.1), CoalitionEvaluation(frozenset({ids[1]}), 0.1), CoalitionEvaluation(frozenset({ids[2]}), 0.1), CoalitionEvaluation(frozenset({ids[3]}), 0.1),
        )
        # An incomplete coalition set is explicit rather than estimated.
        incomplete = self.engine.evaluate(input_for(attacks, spacing=SpacingCondition.SPACED, coalitions=coalitions))
        self.assertEqual(incomplete.shapley.status, ResultStatus.INSUFFICIENT_DATA)
        self.assertEqual(preliminary.recovery_trend.status, ResultStatus.APPLICABLE)
        self.assertLess(preliminary.recovery_trend.tau, 0)

    def test_exact_shapley_and_ordered_sequences(self) -> None:
        first = attack("a-1", 1, state("a", 0.5, 0.5), state("ia", 0.2, 0.2))
        second = attack("b-1", 2, state("b", 1.0, 1.0), state("ib", 0.3, 0.3))
        ids = (first.attack_instance_id, second.attack_instance_id)
        coalitions = (
            CoalitionEvaluation(frozenset(), 0.0),
            CoalitionEvaluation(frozenset({ids[0]}), 0.5),
            CoalitionEvaluation(frozenset({ids[1]}), 0.5),
            CoalitionEvaluation(frozenset(ids), 0.75),
        )
        ab = self.engine.evaluate(input_for((first, second), coalitions=coalitions))
        self.assertEqual(ab.shapley.status, ResultStatus.APPLICABLE)
        self.assertAlmostEqual(sum(ab.shapley.values.values()), 0.75)
        reverse_first = attack("b-1", 1, state("b2", 0.3, 0.3), state("ib2", 0.2, 0.2))
        reverse_second = attack("a-1", 2, state("a2", 0.9, 0.9), state("ia2", 0.2, 0.2))
        ba = self.engine.evaluate(input_for((reverse_first, reverse_second)))
        self.assertEqual(ab.order_effect.attack_order, ("a", "b"))
        self.assertEqual(ba.order_effect.attack_order, ("b", "a"))
        self.assertNotEqual(ab.trajectory.cumulative_vulnerability, ba.trajectory.cumulative_vulnerability)

    def test_determinism_and_session_bootstrap(self) -> None:
        item = attack("a-1", 1, state("a", 0.4, 0.4), state("ia", 0.2, 0.2))
        first = self.engine.evaluate(input_for((item,)))
        second = self.engine.evaluate(input_for((item,)))
        self.assertEqual(first, second)
        interval_a = bootstrap_synergy((first, second), resamples=20, seed=7)
        interval_b = bootstrap_synergy((first, second), resamples=20, seed=7)
        self.assertEqual(interval_a, interval_b)
        self.assertEqual(bootstrap_synergy((first,)).status, ResultStatus.INSUFFICIENT_DATA)

    def test_suspected_session_contamination_blocks_matched_isolated_delta(self) -> None:
        """The ledger record reaches SAEA's actual isolated-delta computation."""
        with tempfile.TemporaryDirectory() as directory:
            observations = ExperimentRunner(
                MockInferenceProvider(default_response="answer"), ObservationStore(Path(directory))
            ).run(specification())
        sequential = next(item for item in observations
                          if item.sequence_id == "case-sequence-1" and item.attack_instance_id == "attack-1")
        isolated = next(item for item in observations
                        if item.condition.value == "isolated_attack" and item.attack_instance_id == "attack-1")
        ledger = assess_isolation(
            record_id="forced-shared-session", sequential_observation_id=sequential.observation_id,
            isolated_observation_id=isolated.observation_id,
            sequential_conversation_id="reused-provider-session",
            isolated_conversation_id="reused-provider-session", provider="mock",
            sequential_metadata={}, isolated_metadata={})
        self.assertIs(ledger.status, IsolationStatus.SUSPECTED_LEAK)
        measurements = tuple(BehaviorMeasurement(item.observation_id,
            {"safety": .8, "helpfulness": .7}, "behavior-v1", "fixture") for item in observations)
        result = self.engine.evaluate(build_saea_input(
            observations, measurements, sequence_id="case-sequence-1", contamination_records=(ledger,)))
        self.assertEqual(result.per_step[0].status, ResultStatus.UNDEFINED)
        self.assertIsNone(result.per_step[0].isolated_delta)
        self.assertEqual(result.per_step[0].reason, "control_contamination_suspected")


if __name__ == "__main__":
    unittest.main()
