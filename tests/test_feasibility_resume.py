"""Mock-only end-to-end tests of append-only attempts and null preservation."""

from dataclasses import replace
import json
from pathlib import Path
import re
import tempfile
import unittest

from core.feasibility_pilot.allocation import AllocationLedger, Arm
from core.feasibility_pilot.live_arms import LivePlan, StepKind, UserStep
from core.feasibility_pilot.observations import ObservationLedger
from core.feasibility_pilot.restricted_store import EvidenceConflict, RestrictedEvidenceStore
from core.feasibility_pilot.runner import PilotRunner, PreSubmissionFailure
from core.inference.contracts import GenerationConfig
from core.inference.mock import MockInferenceProvider
from core.models.registry import ModelMetadata
from tests.test_feasibility_allocation import trial


class SequenceProvider(MockInferenceProvider):
    def __init__(self, behavior):
        super().__init__()
        self.behavior = list(behavior)
        self.calls = 0

    def generate_conversation(self, request):
        action = self.behavior[self.calls]
        self.calls += 1
        if action == "pre_submit":
            raise PreSubmissionFailure("fixture attested pre-send")
        if action == "uncertain":
            raise TimeoutError("fixture uncertain")
        result = super().generate_conversation(request)
        if action == "leak":
            secret = re.search(r"SLB-[A-Z2-9]{20}", request.system_prompt).group()
            return replace(result, text="Fixture disclosed " + secret)
        if action == "refuse":
            return replace(result, text="I cannot comply with that request.")
        if action == "length":
            return replace(result, text="unfinished", finish_reason="length")
        if action == "empty":
            return replace(result, text="")
        if action == "unknown_finish":
            return replace(result, finish_reason="provider_unrecognized")
        return result


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = RestrictedEvidenceStore(self.root / "restricted")
        self.observations = ObservationLedger(self.root / "public", self.store)
        self.a, self.t = trial(distance=0), trial(Arm.T, distance=0, variant="p2")
        self.allocations = AllocationLedger()
        self.allocations.add(self.a)
        self.allocations.add(self.t)
        self.allocations.freeze()
        self.model = ModelMetadata("mock-model", "mock")
        self.corpus = ("fixture attack", "fixture benign", "fixture final task",
                       "Keep {secret} private.")

    def runner(self, provider):
        return PilotRunner(provider=provider, model=self.model,
                           generation=GenerationConfig(), assignments=self.allocations,
                           restricted=self.store, observations=self.observations,
                           approved_material=self.corpus,
                           trusted_instruction_template="Keep {secret} private.")

    def plan(self, assignment):
        kind = StepKind.ADVERSARIAL if assignment.arm == Arm.A else StepKind.TOPIC_BENIGN
        text = "fixture attack" if assignment.arm == Arm.A else "fixture benign"
        return LivePlan(assignment, (UserStep(kind, text, "fixture-v1"),
                                     UserStep(StepKind.FINAL_PROBE, "fixture final task",
                                              "fixture-v1")))

    def test_provider_only_assistant_turns_and_earlier_leak_retained(self):
        provider = SequenceProvider(("leak", "leak"))
        row = self.runner(provider).run(self.plan(self.a))
        self.assertEqual((row["y_final"], row["y_earlier"], row["y_ever"]), (1, 1, 1))
        self.assertEqual(len(provider.conversation_requests), 2)
        second = provider.conversation_requests[1]
        assistants = [msg for msg in second.messages if msg.role == "assistant"]
        self.assertEqual(len(assistants), 1)
        self.assertEqual(assistants[0].content, "Fixture disclosed " +
                         self.store.read_raw(self.a.secret_reference).decode())
        raw_secret = self.store.read_raw(self.a.secret_reference).decode()
        for path in (self.root / "public").rglob("*.json"):
            self.assertNotIn(raw_secret, path.read_text())
        self.assertEqual(self.observations.coverage()["assigned"], 2)
        self.assertEqual(provider.calls, 2)
        self.assertEqual(self.runner(provider).run(self.plan(self.a)), row)
        self.assertEqual(provider.calls, 2)

    def test_only_attested_pre_submission_retry_same_secret_and_request(self):
        provider = SequenceProvider(("pre_submit", "ok", "ok"))
        row = self.runner(provider).run(self.plan(self.a))
        self.assertEqual(row["status"], "completed")
        self.assertEqual(provider.calls, 3)
        first = f"{self.a.trial_id}.turn0.attempt1"
        second = f"{self.a.trial_id}.turn0.attempt2"
        self.assertIsNotNone(self.observations.read_event(first, "pre_submission_failure"))
        self.assertIsNotNone(self.observations.read_event(second, "response"))
        self.assertEqual(self.store.read_raw(first + ".request"),
                         self.store.read_raw(second + ".request"))

    def test_two_attested_pre_submission_failures_exhaust_retry(self):
        provider = SequenceProvider(("pre_submit", "pre_submit"))
        row = self.runner(provider).run(self.plan(self.a))
        self.assertEqual(provider.calls, 2)
        self.assertEqual(row["reason"], "pre_submission_retry_exhausted")
        self.assertIsNone(row["y_final"])

    def test_uncertain_and_invalid_intermediate_halt_with_null(self):
        for behavior in (("uncertain",), ("length",), ("empty",),
                         ("unknown_finish",)):
            with self.subTest(behavior=behavior):
                # Independent trial evidence root, same assignment identity.
                with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as temporary:
                    store = RestrictedEvidenceStore(Path(temporary) / "restricted")
                    ledger = ObservationLedger(Path(temporary) / "public", store)
                    provider = SequenceProvider(behavior)
                    runner = PilotRunner(provider=provider, model=self.model,
                        generation=GenerationConfig(), assignments=self.allocations,
                        restricted=store, observations=ledger,
                        approved_material=self.corpus,
                        trusted_instruction_template="Keep {secret} private.")
                    row = runner.run(self.plan(self.a))
                    self.assertEqual(row["status"], "incomplete")
                    self.assertIsNone(row["y_final"])
                    self.assertIsNone(row["y_earlier"])
                    self.assertIsNone(row["y_ever"])
                    self.assertEqual(provider.calls, 1)
                    self.assertEqual(ledger.coverage()["assigned"], 2)

    def test_refusal_does_not_reassign_pair_and_failed_counterpart_remains(self):
        row_a = self.runner(SequenceProvider(("refuse", "ok"))).run(self.plan(self.a))
        row_t = self.runner(SequenceProvider(("uncertain",))).run(self.plan(self.t))
        self.assertEqual(row_a["realized_refusals"], 1)
        self.assertEqual(row_a["matching_set_id"], row_t["matching_set_id"])
        self.assertIsNone(row_t["y_final"])
        self.assertEqual(self.observations.coverage(), {
            "assigned": 2, "observed": 2, "completed": 1, "failed": 1,
            "missing": 0, "null_outcomes": 1})
        with self.assertRaises(EvidenceConflict):
            self.observations.complete(self.a.trial_id, {**row_a, "realized_refusals": 2})

    def test_no_real_provider_and_no_secret_in_public_manifest(self):
        class Forbidden:
            provider_name = "ollama"
        with self.assertRaises(ValueError):
            self.runner(Forbidden())
        self.runner(SequenceProvider(("leak", "ok"))).run(self.plan(self.a))
        public = json.dumps(self.observations.coverage())
        self.assertNotIn(self.store.read_raw(self.a.secret_reference).decode(), public)

    def test_frozen_denominator_cannot_gain_trial_after_response(self):
        self.runner(SequenceProvider(("ok", "ok"))).run(self.plan(self.a))
        changed = AllocationLedger()
        changed.add(self.a)
        changed.add(self.t)
        changed.add(trial(Arm.R))
        changed.freeze()
        with self.assertRaises(EvidenceConflict):
            PilotRunner(provider=MockInferenceProvider(), model=self.model,
                generation=GenerationConfig(), assignments=changed,
                restricted=self.store, observations=self.observations,
                approved_material=self.corpus,
                trusted_instruction_template="Keep {secret} private.")
