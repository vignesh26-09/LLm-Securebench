"""Deterministic tests for semantic interfaces and exploratory DQI components."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from core.dataset.models import Dataset, DatasetRecord
from core.dataset.quality import (
    DqiWeights,
    analyze_category_balance,
    calculate_coverage_statistics,
    calculate_dqi,
    difficulty_distribution,
    estimate_novelty,
    normalized_entropy,
)
from core.dataset.semantic import cosine_similarity, embed_dataset_prompts, find_near_duplicates


class FakeEmbeddingProvider:
    model_name = "fake-cpu"

    def embed(self, texts: list[str], *, batch_size: int = 32) -> tuple[tuple[float, ...], ...]:
        mapping = {"one": (1.0, 0.0), "near-one": (0.98, 0.02), "other": (0.0, 1.0)}
        return tuple(mapping[text] for text in texts)


class SemanticDatasetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = Dataset((
            DatasetRecord(id="a", prompt="one", category="alpha", difficulty="easy"),
            DatasetRecord(id="b", prompt="near-one", category="alpha", difficulty="hard"),
            DatasetRecord(id="c", prompt="other", category="beta", difficulty="hard"),
            DatasetRecord(id="d", prompt=None),
        ))

    def test_cosine_and_near_duplicates(self) -> None:
        self.assertEqual(cosine_similarity((1.0, 0.0), (0.0, 1.0)), 0.0)
        vectors = embed_dataset_prompts(self.dataset, FakeEmbeddingProvider(), batch_size=2)
        self.assertEqual(vectors[-1], None)
        pairs = find_near_duplicates(vectors, threshold=0.9)
        self.assertEqual([(pair.first_index, pair.second_index) for pair in pairs], [(0, 1)])

    def test_coverage_distributions_and_balance(self) -> None:
        coverage = calculate_coverage_statistics(self.dataset)
        self.assertEqual(coverage.prompt_coverage, 0.75)
        self.assertEqual(difficulty_distribution(self.dataset), {"easy": 1, "hard": 2})
        balance = analyze_category_balance(self.dataset)
        self.assertEqual(balance.counts, {"alpha": 2, "beta": 1})
        self.assertGreater(balance.normalized_entropy, 0.9)
        self.assertEqual(normalized_entropy(["only", "only"]), 0.0)

    def test_novelty_and_configurable_dqi(self) -> None:
        embeddings = ((1.0, 0.0), (1.0, 0.0), (0.0, 1.0), None)
        self.assertAlmostEqual(estimate_novelty(embeddings), 1 / 6)
        dqi = calculate_dqi(self.dataset, embeddings=embeddings, weights=DqiWeights(novelty=2.0))
        self.assertGreaterEqual(dqi.score, 0.0)
        self.assertLessEqual(dqi.score, 1.0)
        self.assertEqual(dqi.components["coverage"], 0.75)
        self.assertAlmostEqual(dqi.components["novelty"], 1 / 6)

    def test_processor_cli_runs_end_to_end(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "scripts.process_dataset", "data/raw/example.json"],
            cwd=root, text=True, capture_output=True, check=True,
        )
        summary = json.loads(result.stdout)
        self.assertEqual(summary["statistics"]["record_count"], 3)
        self.assertEqual(summary["duplicates"]["exact_group_count"], 1)
