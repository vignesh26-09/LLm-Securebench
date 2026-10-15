"""Six live schedules cannot carry attacker-authored assistant turns."""

import unittest
from pathlib import Path
import tempfile

from core.feasibility_pilot.allocation import AllocationLedger, Arm
from core.feasibility_pilot.live_arms import LivePlan, StepKind, UserStep, realized_refusal
from core.feasibility_pilot.observations import ObservationLedger
from core.feasibility_pilot.restricted_store import RestrictedEvidenceStore
from core.feasibility_pilot.runner import PilotRunner
from core.inference.contracts import GenerationConfig
from core.inference.mock import MockInferenceProvider
from core.models.registry import ModelMetadata
from tests.test_feasibility_allocation import trial


def step(kind, text="harmless fixture text"):
    return UserStep(kind, text, "fixture-script")


class LiveArmTests(unittest.TestCase):
    def test_six_live_arm_contracts(self):
        exposure = {Arm.B1: StepKind.GENERIC_BENIGN,
                    Arm.T: StepKind.TOPIC_BENIGN,
                    Arm.R: StepKind.REFUSAL_INTENDED,
                    Arm.A: StepKind.ADVERSARIAL,
                    Arm.I: StepKind.ADVERSARIAL}
        for arm in (Arm.B0, Arm.B1, Arm.T, Arm.R, Arm.A, Arm.I):
            with self.subTest(arm=arm):
                steps = () if arm == Arm.B0 else (step(exposure[arm]),)
                if arm == Arm.I:
                    steps = (step(StepKind.NEUTRAL),) + steps
                plan = LivePlan(trial(arm, None if arm == Arm.B0 else 0),
                                steps + (step(StepKind.FINAL_PROBE),))
                self.assertEqual(plan.assignment.arm, arm)
                self.assertTrue(all(isinstance(item, UserStep) for item in plan.steps))
        with self.assertRaises(ValueError):
            LivePlan(trial(Arm.I, 0), (step(StepKind.ADVERSARIAL),
                                       step(StepKind.FINAL_PROBE)))
        self.assertTrue(realized_refusal("I cannot do that."))
        self.assertFalse(realized_refusal("A normal answer."))

    def test_all_six_live_arms_execute_only_provider_assistant_turns(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as temporary:
            store = RestrictedEvidenceStore(Path(temporary) / "restricted")
            ledger = ObservationLedger(Path(temporary) / "public", store)
            allocation = AllocationLedger()
            plans = []
            kind_by_arm = {Arm.B1: StepKind.GENERIC_BENIGN,
                           Arm.T: StepKind.TOPIC_BENIGN,
                           Arm.R: StepKind.REFUSAL_INTENDED,
                           Arm.A: StepKind.ADVERSARIAL,
                           Arm.I: StepKind.ADVERSARIAL}
            for arm in (Arm.B0, Arm.B1, Arm.T, Arm.R, Arm.A, Arm.I):
                assignment = trial(arm, None if arm == Arm.B0 else 0,
                                   variant="p2" if arm == Arm.T else "p1")
                allocation.add(assignment)
                exposure = () if arm == Arm.B0 else (step(kind_by_arm[arm],
                                                         "fixture exposure"),)
                if arm == Arm.I:
                    exposure = (step(StepKind.NEUTRAL, "fixture neutral"),) + exposure
                plans.append(LivePlan(assignment, exposure +
                                      (step(StepKind.FINAL_PROBE, "fixture final task"),)))
            allocation.freeze()
            provider = MockInferenceProvider(default_response="fixture provider answer")
            runner = PilotRunner(provider=provider, model=ModelMetadata("mock-model", "mock"),
                generation=GenerationConfig(), assignments=allocation,
                restricted=store, observations=ledger,
                approved_material=("fixture exposure", "fixture neutral",
                                   "fixture final task", "Keep {secret} private."),
                trusted_instruction_template="Keep {secret} private.")
            for plan in plans:
                row = runner.run(plan)
                self.assertEqual(row["status"], "completed")
                self.assertEqual(row["y_final"], 0)
                requests = [request for request in provider.conversation_requests
                            if request.conversation_id == plan.assignment.trial_id]
                self.assertEqual(len(requests), len(plan.steps))
                for request in requests:
                    self.assertTrue(all(message.content == "fixture provider answer"
                                        for message in request.messages if message.role == "assistant"))
            self.assertEqual(ledger.coverage()["assigned"], 6)
            self.assertEqual(len(ledger.live_primary_rows()), 2)

