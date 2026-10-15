"""Scientific retention status cannot be inferred from request-level evidence."""

import unittest

from core.feasibility_pilot.context import (ContextEvidence, ScientificContextStatus,
                                            assess_context, pair_validity_warning)


class ContextTests(unittest.TestCase):
    def test_unobservable_rendering_stays_unverifiable(self):
        assessed = assess_context(ContextEvidence(evidence_reference="request-history-hash"))
        self.assertEqual(assessed.status, ScientificContextStatus.RETENTION_UNVERIFIABLE)

    def test_known_loss_takes_precedence(self):
        assessed = assess_context(ContextEvidence(
            rendered_prompt_contains_required_content=True,
            effective_retention_confirmed=True, required_content_known_lost=True,
            evidence_reference="truncation-log"))
        self.assertEqual(assessed.status, ScientificContextStatus.TRUNCATED_KNOWN)

    def test_affirmative_post_template_evidence_requires_reference(self):
        positive = ContextEvidence(True, True, evidence_reference="rendered-prompt-hash")
        self.assertEqual(assess_context(positive).status,
                         ScientificContextStatus.RETAINED_VERIFIED)
        self.assertEqual(assess_context(ContextEvidence(True, True)).status,
                         ScientificContextStatus.RETENTION_UNVERIFIABLE)

    def test_asymmetric_a_t_status_warns(self):
        adversarial = assess_context(ContextEvidence(required_content_known_lost=True))
        control = assess_context(ContextEvidence())
        self.assertTrue(pair_validity_warning(adversarial, control))
        self.assertFalse(pair_validity_warning(control, control))
