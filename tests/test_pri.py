"""Deterministic CPU-only tests for PRI Mode A/B profile infrastructure."""

import unittest

from core.draa import EvidenceExtractor
from core.draa.models import DRAAMode, SeverityEvidence
from core.pri.compatibility import compare
from core.pri.diagnostics import summarize
from core.pri.models import (
    BenchmarkPopulationIdentity, HierarchyIdentifiers, PRIProfileCell,
    PRIProfileMode, PRIReferenceArtifact, PRIStatus, SystemConfigurationIdentity,
)
from core.pri.profile import PRIProfileBuilder
from core.pri.serialization import dumps, loads


def configuration(**changes: object) -> SystemConfigurationIdentity:
    values = {"model_id": "mock", "provider": "mock", "model_version": "v1", "generation": {"temperature": 0.0}, "seeds": (7,), "system_context_id": "system-v1", "harness_id": "harness-v1", "policy_id": "policy-v1", "taxonomy_id": "tax-v1"}
    values.update(changes)
    return SystemConfigurationIdentity(**values)


def population(**changes: object) -> BenchmarkPopulationIdentity:
    values = {"benchmark_id": "bench", "benchmark_version": "v1", "benchmark_hash": "hash", "dataset_id": "data", "dataset_version": "v1", "taxonomy_version": "tax-v1", "threat_model": "injection", "requested_categories": ("injection", "leakage")}
    values.update(changes)
    return BenchmarkPopulationIdentity(**values)


def cell(**changes: object) -> PRIProfileCell:
    values = {"benchmark_category": "injection", "observed_construct": None, "source_namespace": "layer1", "source_feature_name": "detector", "value": 0.4, "value_type": "scalar", "units": "detector-native", "orientation": "detector-native", "status": PRIStatus.APPLICABLE, "hierarchy": HierarchyIdentifiers(attack_family_id="family", base_case_id="case", prompt_variant_id="variant", stochastic_run_id="run-1", session_id="session")}
    values.update(changes)
    return PRIProfileCell(**values)


class PRITest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = PRIProfileBuilder()

    def test_minimal_profile_and_identity_preservation(self) -> None:
        profile = self.builder.build(configuration(), population(), cells=(cell(),), benchmark_run_ids=("run",))
        self.assertEqual(profile.status, PRIStatus.UNCALIBRATED)
        self.assertIsNone(profile.scalar_pri)
        self.assertEqual(profile.configuration.generation["temperature"], 0.0)
        self.assertEqual(profile.population.benchmark_hash, "hash")
        self.assertEqual(profile.coverage.hierarchy_counts["stochastic_run_id"], 1)

    def test_partial_coverage_and_missing_data_remain_explicit(self) -> None:
        profile = self.builder.build(configuration(system_context_id=None), population(), cells=(cell(status=PRIStatus.FAILED, value=None),))
        self.assertEqual(profile.coverage.category_statuses["injection"], PRIStatus.APPLICABLE)
        self.assertEqual(profile.coverage.category_statuses["leakage"], PRIStatus.NOT_EVALUATED)
        self.assertIsNone(profile.cells[0].value)
        self.assertIsNone(profile.configuration.system_context_id)

    def test_draa_ingestion_preserves_uncalibrated_evidence_and_duplicate_warning(self) -> None:
        draa = EvidenceExtractor().build(mode=DRAAMode.FEATURE_EXTRACTION, identities={"evaluation_id": "eval"})
        first = self.builder.build(configuration(), population(), draa_records=(draa,))
        self.assertEqual(first.status, PRIStatus.UNCALIBRATED)
        self.assertIsNone(draa.risk_score)
        self.assertEqual(first.cells, ())
        # A feature with matching provenance is not silently double counted.
        draa = EvidenceExtractor().build(identities={"evaluation_id": "eval"}, rc={"rc_auc_raw": 0.8, "applicability": "applicable", "artifact_id": "source-1"})
        direct = cell(source_namespace="rc", source_feature_name="rc_auc_raw", value=0.8, hierarchy=HierarchyIdentifiers(), provenance={"artifact_id": "source-1"})
        duplicate = self.builder.build(configuration(), population(), cells=(direct,), draa_records=(draa,))
        self.assertEqual(len(duplicate.cells), 1)
        self.assertIn("duplicate_upstream_provenance", duplicate.warnings)

    def test_statuses_diagnostics_and_round_trip(self) -> None:
        profile = self.builder.build(configuration(), population(), mode=PRIProfileMode.DESCRIPTIVE_DIAGNOSTICS, cells=(cell(), cell(source_namespace="layer2", source_feature_name="judge", value=None, status=PRIStatus.FAILED, uncertainty={"reason": "timeout"})))
        diagnostic = summarize(profile)
        self.assertEqual(diagnostic.status_counts["applicable"], 1)
        self.assertEqual(diagnostic.uncertainty_available, 1)
        self.assertEqual(loads(dumps(profile)), profile)

    def test_compatibility_and_reference_artifact(self) -> None:
        left = self.builder.build(configuration(), population())
        self.assertEqual(compare(left, self.builder.build(configuration(), population())).status, "compatible")
        self.assertEqual(compare(left, self.builder.build(configuration(), population(benchmark_hash="other"))).status, "incompatible")
        self.assertEqual(compare(left, self.builder.build(configuration(), population(taxonomy_version=None))).status, "unknown")
        artifact = PRIReferenceArtifact("artifact", "pri-v1", "hash", "tax", "injection")
        self.assertEqual(artifact.validation_status, "unvalidated")


if __name__ == "__main__":
    unittest.main()
