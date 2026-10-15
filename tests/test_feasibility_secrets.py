"""Secret distribution, uniqueness and retry binding use disposable records."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.feasibility_pilot.restricted_store import EvidenceConflict, RestrictedEvidenceStore
from core.feasibility_pilot.secrets import (ALPHABET, PAYLOAD_LENGTH, PREFIX,
                                            SecretAllocator)


class SecretTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=r"F:\SecureLLM.tmp")
        self.addCleanup(self.temporary.cleanup)
        self.store = RestrictedEvidenceStore(Path(self.temporary.name) / "restricted")
        self.allocator = SecretAllocator(self.store)
        self.corpus = ("approved harmless attack", "approved benign probe", "approved filler")

    def test_frozen_distribution_fresh_trials_and_same_trial_retry(self):
        self.assertEqual(len(ALPHABET), 32)
        first = self.allocator.bind("trial_1", self.corpus)
        second = self.allocator.bind("trial_2", self.corpus)
        value1 = self.allocator.read_for_restricted_checker(first)
        value2 = self.allocator.read_for_restricted_checker(second)
        self.assertEqual(len(value1), len(PREFIX) + PAYLOAD_LENGTH)
        self.assertTrue(value1.startswith(PREFIX))
        self.assertTrue(all(char in ALPHABET for char in value1[len(PREFIX):]))
        self.assertNotEqual(value1, value2)
        self.assertEqual(first, self.allocator.bind("trial_1", self.corpus))
        self.assertNotIn(value1, repr(first))
        with self.assertRaises(EvidenceConflict):
            self.allocator.bind("trial_1", ("different approved corpus",))

    def test_collision_and_corpus_occurrence_are_redrawn(self):
        in_corpus = PREFIX + "A" * PAYLOAD_LENGTH
        accepted = PREFIX + "B" * PAYLOAD_LENGTH
        with patch("core.feasibility_pilot.secrets._candidate", side_effect=[in_corpus, accepted]):
            binding = self.allocator.bind("trial_1", (*self.corpus, in_corpus))
        self.assertEqual(binding.rejected_draws, 1)
        self.assertEqual(self.allocator.read_for_restricted_checker(binding), accepted)
        later = PREFIX + "C" * PAYLOAD_LENGTH
        with patch("core.feasibility_pilot.secrets._candidate", side_effect=[accepted, later]):
            second = self.allocator.bind("trial_2", (*self.corpus, in_corpus))
        self.assertEqual(second.rejected_draws, 1)
        self.assertEqual(self.allocator.read_for_restricted_checker(second), later)

    def test_scripted_or_public_material_with_bound_secret_is_rejected(self):
        binding = self.allocator.bind("trial_1", self.corpus)
        secret = self.allocator.read_for_restricted_checker(binding)
        with self.assertRaises(Exception):
            self.store.assert_public_safe("scripted assistant: " + secret)
