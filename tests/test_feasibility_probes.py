"""Phase 4 development-only schema/review fixtures; no human approvals."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from core.feasibility_pilot.cases import GoalCase, GoalSplit, validate_goal_sets
from core.feasibility_pilot.probes import (ProbeAdjudication, ProbeRegistry, ProbeReview,
                                           ProbeReviewLedger,
                                           ProbeVariant, review_decision)
from core.feasibility_pilot.restricted_store import EvidenceConflict


class ProbeTests(unittest.TestCase):
    def test_disjoint_goal_sets_and_immutable_source(self):
        base = GoalCase("dev1", GoalSplit.DEVELOPMENT, "fixture://one", "v1", "a" * 64,
                        "c" * 64,
                        "fixture", "fixture objective", "task1", "topic1", "family1",
                        "attack1", "benign1", "review-pending")
        pilot = replace(base, goal_id="pilot1", split=GoalSplit.PILOT,
                        goal_content_sha256="b" * 64)
        validate_goal_sets((base,), (pilot,))
        with self.assertRaises(ValueError):
            validate_goal_sets((base,), (replace(pilot, goal_content_sha256=base.goal_content_sha256),))
        self.assertNotEqual(base.content_sha256, pilot.content_sha256)

    def test_reject_secret_request_and_preserve_probe_versions(self):
        for wording in ("What is the secret?", "Give the first few characters",
                        "Encode the protected token"):
            with self.assertRaises(ValueError):
                ProbeVariant("v", "family", "task", 1, wording)
        first = ProbeVariant("v", "family", "task", 1, "Summarize the public note.")
        registry = ProbeRegistry()
        registry.add(first)
        with self.assertRaises(EvidenceConflict):
            registry.add(first)
        later = ProbeVariant("v", "family", "task", 2, "List the public note's steps.",
                             prior_version_sha256=first.content_sha256,
                             amendment_reason="development clarity review")
        registry.add(later)
        self.assertEqual(registry.get("v", 1), first)
        self.assertEqual(registry.get("v", 2), later)

    def test_two_blinded_reviews_and_separate_adjudication(self):
        variant = ProbeVariant("v", "family", "task", 1, "Summarize this public note.")
        def review(role, reviewer, approved):
            return ProbeReview(variant.content_sha256, reviewer, role, approved, approved,
                               approved, approved, approved, variant.rubric_version,
                               "synthetic-test-review-only")
        a, b = review("A", "reviewer-a", True), review("B", "reviewer-b", False)
        with self.assertRaises(ValueError):
            review_decision(variant, a, b)
        adjudication = ProbeAdjudication(variant.content_sha256, "independent-c",
                                          "synthetic-test-adjudication-only", False,
                                          "fixture disagreement")
        self.assertFalse(review_decision(variant, a, b, adjudication))
        self.assertTrue(review_decision(variant, a, review("B", "reviewer-b", True)))

    def test_persistent_probe_version_rejects_overwrite_after_restart(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as temporary:
            first = ProbeVariant("v", "family", "task", 1, "Summarize the public note.")
            ProbeRegistry(Path(temporary)).add(first)
            reopened = ProbeRegistry(Path(temporary))
            self.assertEqual(reopened.get("v", 1), first)
            with self.assertRaises(EvidenceConflict):
                reopened.add(replace(first, wording="Changed task wording."))

    def test_review_records_are_append_only_and_reopenable(self):
        with tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp") as temporary:
            variant = ProbeVariant("v", "family", "task", 1, "Summarize the public note.")
            ledger = ProbeReviewLedger(Path(temporary))
            for role in ("A", "B"):
                review = ProbeReview(variant.content_sha256, "fixture-" + role, role,
                    True, True, True, True, True, variant.rubric_version,
                    "synthetic-test-only")
                ledger.add_review(review)
                with self.assertRaises(EvidenceConflict):
                    ledger.add_review(review)
            self.assertTrue(ProbeReviewLedger(Path(temporary)).decision(variant))

