"""Mock-only exchange-distance schedules; no real pilot material or model calls."""

import json
import logging
from pathlib import Path
import re
import tempfile
import unittest

from core.feasibility_pilot.allocation import AllocationLedger, Arm
from core.feasibility_pilot.distance import build_distance_schedule, validate_frozen_schedule
from core.feasibility_pilot.live_arms import LivePlan, StepKind, UserStep
from core.feasibility_pilot.observations import ObservationLedger
from core.feasibility_pilot.restricted_store import RestrictedEvidenceStore
from core.feasibility_pilot.runner import PilotRunner
from core.feasibility_pilot.scripted_arm import ScriptedAssistantTurn, ScriptedPlan
from core.inference.contracts import GenerationConfig
from core.inference.mock import MockInferenceProvider
from core.models.registry import ModelMetadata
from tests.test_feasibility_allocation import trial
from tests.test_feasibility_resume import SequenceProvider


def step(kind, text, script="fixture-v1"):
    return UserStep(kind, text, script)


def live_plan(assignment):
    exposure_kind = StepKind.ADVERSARIAL if assignment.arm == Arm.A else StepKind.TOPIC_BENIGN
    exposure = step(exposure_kind, "fixture exposure")
    fillers = tuple(step(StepKind.FILLER, f"fixture benign filler {index}")
                    for index in range(assignment.distance or 0))
    return LivePlan(assignment, (exposure,) + fillers +
                    (step(StepKind.FINAL_PROBE, "fixture legitimate task"),))


class DistanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = RestrictedEvidenceStore(self.root / "restricted")
        self.ledger = ObservationLedger(self.root / "public", self.store)
        self.model = ModelMetadata("mock-model", "mock")
        self.corpus = ("fixture exposure", "fixture neutral", "fixture legitimate task",
                       *(f"fixture benign filler {index}" for index in range(5)),
                       "Keep {secret} private.")

    def runner(self, allocations, provider, schedules=None):
        return PilotRunner(provider=provider, model=self.model,
            generation=GenerationConfig(), assignments=allocations,
            restricted=self.store, observations=self.ledger,
            approved_material=self.corpus,
            trusted_instruction_template="Keep {secret} private.",
            distance_schedules=schedules)

    def test_exact_zero_two_five_complete_exchanges_and_final_position(self):
        assignments = AllocationLedger()
        plans = []
        schedules = {}
        for distance in (0, 2, 5):
            for arm, variant in ((Arm.A, "p1"), (Arm.T, "p2")):
                assignment = trial(arm, distance, variant)
                assignments.add(assignment)
                plan = live_plan(assignment)
                plans.append(plan)
                schedules[assignment.trial_id] = build_distance_schedule(plan)
        assignments.freeze()
        provider = MockInferenceProvider(default_response="fixture defender answer")
        runner = self.runner(assignments, provider, schedules)
        for plan in plans:
            distance = plan.assignment.distance
            result = runner.run(plan)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["distance"], distance)
            self.assertEqual(result["planned_filler_exchanges"], distance)
            self.assertEqual(result["realized_complete_filler_exchanges"], distance)
            requests = [request for request in provider.conversation_requests
                        if request.conversation_id == plan.assignment.trial_id]
            self.assertEqual(len(requests), distance + 2)
            self.assertEqual(requests[-1].messages[-1].content, "fixture legitimate task")
            self.assertEqual(sum(message.role == "assistant" for message in requests[-1].messages),
                             distance + 1)
            self.assertTrue(all(message.content == "fixture defender answer"
                                for message in requests[-1].messages if message.role == "assistant"))
        self.assertEqual(self.ledger.coverage()["assigned"], 6)
        self.assertEqual(self.ledger.coverage()["completed"], 6)

    def test_failed_intermediate_filler_is_not_completed_or_retried(self):
        a, t = trial(Arm.A, 5, "p1"), trial(Arm.T, 5, "p2")
        assignments = AllocationLedger()
        assignments.add(a)
        assignments.add(t)
        assignments.freeze()
        provider = SequenceProvider(("ok", "ok", "ok", "length"))
        row = self.runner(assignments, provider).run(live_plan(a))
        self.assertEqual(provider.calls, 4)
        self.assertEqual(row["distance"], 5)
        self.assertEqual(row["planned_filler_exchanges"], 5)
        self.assertEqual(row["realized_complete_filler_exchanges"], 2)
        self.assertIsNone(row["y_final"])
        self.assertIsNone(row["y_earlier"])
        self.assertEqual(row["matching_set_id"], t.matching_set_id)
        self.assertEqual(self.ledger.coverage()["assigned"], 2)
        self.assertEqual(self.ledger.coverage()["missing"], 1)
        self.assertIsNone(self.ledger.observation(t.trial_id))

    def test_schedule_rejects_missing_extra_or_reordered_fillers(self):
        assignment = trial(Arm.A, 2)
        good = live_plan(assignment)
        schedule = build_distance_schedule(good)
        validate_frozen_schedule(good, schedule)
        missing = LivePlan(assignment, (good.steps[0], good.steps[1], good.steps[-1]))
        with self.assertRaises(ValueError):
            build_distance_schedule(missing)
        extra = LivePlan(assignment, good.steps[:-1] +
                         (step(StepKind.FILLER, "extra filler"), good.steps[-1]))
        with self.assertRaises(ValueError):
            build_distance_schedule(extra)
        changed = LivePlan(assignment, (step(StepKind.ADVERSARIAL, "changed exposure"),)
                           + good.steps[1:])
        with self.assertRaises(ValueError):
            validate_frozen_schedule(changed, schedule)
        misplaced = LivePlan(assignment, (good.steps[0], good.steps[1],
                                           step(StepKind.TOPIC_BENIGN, "misplaced"),
                                           good.steps[2], good.steps[-1]))
        with self.assertRaises(ValueError):
            build_distance_schedule(misplaced)

    def test_b0_not_applicable_and_scripted_s_diagnostic(self):
        b0 = trial(Arm.B0, None)
        b0_plan = LivePlan(b0, (step(StepKind.FINAL_PROBE, "fixture legitimate task"),))
        self.assertIsNone(build_distance_schedule(b0_plan).assigned_distance)
        s = trial(Arm.S, 2)
        s_plan = ScriptedPlan(s, step(StepKind.TOPIC_BENIGN, "fixture exposure"),
            ScriptedAssistantTurn("fixture scripted text", script_version="fixture-v1"),
            (step(StepKind.FILLER, "fixture benign filler 0"),
             step(StepKind.FILLER, "fixture benign filler 1"),
             step(StepKind.FINAL_PROBE, "fixture legitimate task")))
        allocations = AllocationLedger()
        allocations.add(b0)
        allocations.add(s)
        allocations.freeze()
        corpus = self.corpus + ("fixture scripted text",)
        provider = MockInferenceProvider(default_response="fixture defender answer")
        runner = PilotRunner(provider=provider, model=self.model,
            generation=GenerationConfig(), assignments=allocations,
            restricted=self.store, observations=self.ledger,
            approved_material=corpus, trusted_instruction_template="Keep {secret} private.")
        b0_row = runner.run(b0_plan)
        s_row = runner.run(s_plan)
        self.assertIsNone(b0_row["distance"])
        self.assertEqual(b0_row["realized_complete_filler_exchanges"], 0)
        self.assertEqual(s_row["realized_complete_filler_exchanges"], 2)
        self.assertEqual(s_row["evidence_class"], "scripted_mechanism")
        self.assertEqual(self.ledger.live_primary_rows(), ())
        self.assertEqual(self.ledger.verified_context_primary_rows(), ())

    def test_isolated_attack_diagnostic_distance_five(self):
        isolated = trial(Arm.I, 5)
        plan = LivePlan(isolated,
            (step(StepKind.NEUTRAL, "fixture neutral"),
             step(StepKind.ADVERSARIAL, "fixture exposure"))
            + tuple(step(StepKind.FILLER, f"fixture benign filler {index}")
                    for index in range(5))
            + (step(StepKind.FINAL_PROBE, "fixture legitimate task"),))
        allocations = AllocationLedger()
        allocations.add(isolated)
        allocations.freeze()
        runner = self.runner(allocations,
                             MockInferenceProvider(default_response="fixture defender answer"))
        row = runner.run(plan)
        self.assertEqual(row["realized_complete_filler_exchanges"], 5)
        self.assertEqual(row["distance"], 5)
        self.assertFalse(row["live_primary_eligible_arm"])
        self.assertEqual(self.ledger.live_primary_rows(), ())

    def test_raw_secret_stays_out_of_public_records_and_errors(self):
        a, t = trial(Arm.A, 0, "p1"), trial(Arm.T, 0, "p2")
        allocations = AllocationLedger()
        allocations.add(a)
        allocations.add(t)
        allocations.freeze()

        class FailingMock(MockInferenceProvider):
            def generate_conversation(self, request):
                secret = re.search(r"SLB-[A-Z2-9]{20}", request.system_prompt).group()
                raise RuntimeError("fixture failure " + secret)

        captured = []
        class Capture(logging.Handler):
            def emit(self, record):
                captured.append(record.getMessage())
        handler = Capture()
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            row = self.runner(allocations, FailingMock()).run(live_plan(a))
        finally:
            root_logger.removeHandler(handler)
        secret = self.store.read_raw(a.secret_reference).decode()
        self.assertIsNone(row["y_final"])
        self.assertNotIn(secret, json.dumps(row))
        self.assertTrue(all(secret not in message for message in captured))
        for path in (self.root / "public").rglob("*.json"):
            self.assertNotIn(secret, path.read_text(encoding="utf-8"))
