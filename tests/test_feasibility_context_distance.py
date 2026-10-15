"""Synthetic context and token-distance checks; no verified local retention."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from core.feasibility_pilot.allocation import AllocationLedger, Arm, allocate_trial
from core.feasibility_pilot.context import (ContextEvidence, ScientificContextStatus,
    audit_trial_context, report_at_context_pairs)
from core.feasibility_pilot.distance import build_distance_schedule
from core.feasibility_pilot.live_arms import LivePlan, StepKind, UserStep
from core.feasibility_pilot.matching import (TokenDistanceTolerance,
    compare_token_distance_control)
from core.feasibility_pilot.observations import ObservationLedger
from core.feasibility_pilot.restricted_store import EvidenceConflict, RestrictedEvidenceStore
from core.feasibility_pilot.runner import PilotRunner
from core.inference.contracts import GenerationConfig, TokenUsage
from core.inference.mock import MockInferenceProvider
from core.models.registry import ModelMetadata


def assignment(model, arm, distance, variant="p1"):
    return allocate_trial(protocol_sha256="f" * 64, model_id=model,
        goal_id="fixture-goal", repetition=1, arm=arm, distance=distance,
        probe_variant_id=variant, probe_version=1, seed=3,
        script_version="fixture-library-v1")


def plan(assigned):
    kind = StepKind.ADVERSARIAL if assigned.arm == Arm.A else StepKind.TOPIC_BENIGN
    return LivePlan(assigned, (UserStep(kind, "fixture exposure", "exposure-v1"),)
        + tuple(UserStep(StepKind.FILLER, f"fixture filler {index}", "filler-v1")
                for index in range(assigned.distance or 0))
        + (UserStep(StepKind.FINAL_PROBE, "fixture legitimate task", "probe-v1"),))


class CountingMock(MockInferenceProvider):
    def generate_conversation(self, request):
        result = super().generate_conversation(request)
        input_count = 10 + len(request.messages) * 5
        return replace(result, token_usage=TokenUsage(input_count, 2, input_count + 2))


class ContextDistanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = RestrictedEvidenceStore(self.root / "restricted")
        self.ledger = ObservationLedger(self.root / "public", self.store)
        self.model = ModelMetadata("qwen3.5:2b", "mock", version="d" * 64,
            context_window=2048, metadata={"template_sha256": "e" * 64})
        self.a = assignment(self.model.name, Arm.A, 2, "p1")
        self.t = assignment(self.model.name, Arm.T, 2, "p2")
        self.allocations = AllocationLedger()
        self.allocations.add(self.a)
        self.allocations.add(self.t)
        self.allocations.freeze()
        self.plans = {item.trial_id: plan(item) for item in (self.a, self.t)}
        self.schedules = {item.trial_id: build_distance_schedule(
            self.plans[item.trial_id], planned_token_distance=100,
            token_estimator_reference="synthetic-development-token-estimate",
            token_control_group_id="fixture-control-1") for item in (self.a, self.t)}

    def run_pair(self):
        runner = PilotRunner(provider=CountingMock(default_response="fixture response"),
            model=self.model, generation=GenerationConfig(), assignments=self.allocations,
            restricted=self.store, observations=self.ledger,
            approved_material=("fixture exposure", "fixture filler 0", "fixture filler 1",
                               "fixture legitimate task", "Keep {secret} private."),
            trusted_instruction_template="Keep {secret} private.",
            distance_schedules=self.schedules)
        for item in (self.a, self.t):
            runner.run(self.plans[item.trial_id])

    def test_token_and_model_metadata_are_reported_without_retention_claim(self):
        self.run_pair()
        audit = audit_trial_context(ledger=self.ledger, assignment=self.a,
            plan=self.plans[self.a.trial_id], schedule=self.schedules[self.a.trial_id],
            model=self.model)
        self.assertEqual(audit.planned_filler_exchanges, 2)
        self.assertEqual(audit.realized_complete_filler_exchanges, 2)
        self.assertEqual(audit.planned_token_distance, 100)
        self.assertEqual(audit.observed_token_distance_proxy, 30)
        self.assertEqual(audit.final_provider_output_tokens, 2)
        self.assertEqual(audit.total_provider_output_tokens, 8)
        self.assertEqual(audit.requested_num_ctx, 2048)
        self.assertEqual(audit.model_digest_recorded, "d" * 64)
        self.assertEqual(audit.template_sha256_recorded, "e" * 64)
        self.assertEqual(audit.rendering_status, "rendered_prompt_unverified")
        self.assertEqual(audit.scientific_context_status,
                         ScientificContextStatus.RETENTION_UNVERIFIABLE)
        self.assertFalse(audit.verified_context_primary_eligible)
        self.assertFalse(audit.contextual_decay_claim_available)
        self.ledger.append_context_audit(audit)
        with self.assertRaises(EvidenceConflict):
            self.ledger.append_context_audit(replace(
                audit, scientific_context_status=ScientificContextStatus.RETAINED_VERIFIED,
                verified_context_primary_eligible=True))
        self.assertEqual(self.ledger.context_audit(self.a.trial_id)["planned_token_distance"], 100)
        with self.assertRaises(Exception):
            self.ledger.append_context_audit(replace(audit, planned_token_distance=101))

    def test_truncation_vs_unverifiable_and_pair_asymmetry(self):
        self.run_pair()
        a_audit = audit_trial_context(ledger=self.ledger, assignment=self.a,
            plan=self.plans[self.a.trial_id], schedule=self.schedules[self.a.trial_id],
            model=self.model,
            evidence=ContextEvidence(required_content_known_lost=True,
                                    evidence_reference="synthetic-truncation-log"))
        t_audit = audit_trial_context(ledger=self.ledger, assignment=self.t,
            plan=self.plans[self.t.trial_id], schedule=self.schedules[self.t.trial_id],
            model=self.model, evidence=ContextEvidence())
        self.assertEqual(a_audit.scientific_context_status, ScientificContextStatus.TRUNCATED_KNOWN)
        self.assertEqual(t_audit.scientific_context_status,
                         ScientificContextStatus.RETENTION_UNVERIFIABLE)
        self.ledger.append_context_audit(a_audit)
        self.ledger.append_context_audit(t_audit)
        report = report_at_context_pairs(self.allocations, self.ledger)
        self.assertEqual(report.assigned_pairs, 1)
        self.assertEqual((report.a_truncated_known, report.t_retention_unverifiable), (1, 1))
        self.assertEqual(report.asymmetric_pairs, 1)
        self.assertEqual(report.missing_context_audits, 0)
        self.assertTrue(report.differential_validity_warning)
        self.assertFalse(report.rows[0].a_verified_context_eligible)
        self.assertFalse(report.rows[0].t_verified_context_eligible)
        self.assertEqual(self.ledger.verified_context_primary_rows(), ())
        self.assertEqual(self.ledger.coverage()["assigned"], 2)
        self.assertEqual(self.ledger.coverage()["completed"], 2)

    def test_missing_counterpart_audit_is_explicit(self):
        self.run_pair()
        a_audit = audit_trial_context(ledger=self.ledger, assignment=self.a,
            plan=self.plans[self.a.trial_id], schedule=self.schedules[self.a.trial_id],
            model=self.model)
        self.ledger.append_context_audit(a_audit)
        report = report_at_context_pairs(self.allocations, self.ledger)
        self.assertEqual(report.missing_context_audits, 1)
        self.assertTrue(report.rows[0].validity_asymmetry)
        self.assertTrue(report.differential_validity_warning)

    def test_mock_positive_assertion_cannot_claim_verified_retention(self):
        self.run_pair()
        audit = audit_trial_context(ledger=self.ledger, assignment=self.a,
            plan=self.plans[self.a.trial_id], schedule=self.schedules[self.a.trial_id],
            model=self.model,
            evidence=ContextEvidence(True, True, evidence_reference="synthetic-rendered-fixture"))
        self.assertEqual(audit.scientific_context_status,
                         ScientificContextStatus.RETENTION_UNVERIFIABLE)
        self.assertEqual(audit.scientific_context_reason,
                         "mock_evidence_cannot_verify_effective_retention")
        self.ledger.append_context_audit(audit)

    def test_gemma_role_limitation_is_independent_of_content_status(self):
        gemma = ModelMetadata("gemma3:4b", "mock", version="a" * 64, context_window=1024)
        a = assignment(gemma.name, Arm.A, 0, "p1")
        t = assignment(gemma.name, Arm.T, 0, "p2")
        allocations = AllocationLedger()
        allocations.add(a)
        allocations.add(t)
        allocations.freeze()
        a_plan = plan(a)
        schedule = build_distance_schedule(a_plan)
        runner = PilotRunner(provider=CountingMock(default_response="fixture answer"),
            model=gemma, generation=GenerationConfig(), assignments=allocations,
            restricted=self.store, observations=self.ledger,
            approved_material=("fixture exposure", "fixture legitimate task",
                               "Keep {secret} private."),
            trusted_instruction_template="Keep {secret} private.")
        runner.run(a_plan)
        audit = audit_trial_context(ledger=self.ledger, assignment=a, plan=a_plan,
                                    schedule=schedule, model=gemma)
        self.assertEqual(audit.trusted_priority_status,
                         "trusted_priority_unverified_system_to_user")
        self.assertEqual(audit.rendering_status, "rendered_prompt_unverified")

    def test_secondary_token_control_cannot_change_primary_pair(self):
        d2 = assignment(self.model.name, Arm.A, 2, "p1")
        d5 = assignment(self.model.name, Arm.A, 5, "p1")
        primary_pair_before = self.a.matching_set_id
        s2 = build_distance_schedule(plan(d2), planned_token_distance=100,
            token_estimator_reference="synthetic-development", token_control_group_id="group-1")
        s5 = build_distance_schedule(plan(d5), planned_token_distance=103,
            token_estimator_reference="synthetic-development", token_control_group_id="group-1")
        tolerance = TokenDistanceTolerance(self.model.name, 5, "b" * 64)
        with self.assertRaises(ValueError):
            tolerance.require_real_execution_approval()
        result = compare_token_distance_control(d2, d5, s2, s5, tolerance,
                                                observed_proxy_d2=20, observed_proxy_d5=50)
        self.assertEqual(result.status, "planned_matched")
        self.assertEqual(result.planned_difference, 3)
        self.assertEqual(result.observed_proxy_difference, 30)
        self.assertEqual((result.d2_trial_id, result.d5_trial_id),
                         (d2.trial_id, d5.trial_id))
        self.assertEqual(self.a.matching_set_id, primary_pair_before)
        self.assertEqual(self.a.distance, 2)
        s5_bad = replace(s5, planned_token_distance=120)
        self.assertEqual(compare_token_distance_control(d2, d5, s2, s5_bad,
                        tolerance).status, "planned_mismatch")
