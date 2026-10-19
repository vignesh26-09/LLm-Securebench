"""Chart-shaped records test rendering contracts, not empirical findings."""
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

from core.persistence.database import Base, make_engine
from core.persistence.models import ScientificRecordEntity
from core.reporting.charts import generate_chart


ELIGIBLE_SHAPE = {"data_origin": "real_persisted", "reporting_class": "phase1_scientific"}
LINE_TYPES = ("recovery_trajectory", "saea_trajectory", "latency_per_turn")


class ReportingLineTests(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)

    def tearDown(self):
        self.engine.dispose()
        self.temp.cleanup()

    def add(self, identity, family, payload, status="applicable", provenance=None):
        with Session(self.engine) as session:
            session.add(ScientificRecordEntity(
                id=identity, family=family, schema_version="chart-contract-test-v1",
                scope="TEST", status=status, payload=payload,
                provenance=ELIGIBLE_SHAPE if provenance is None else provenance))
            session.commit()

    def generate(self, kind):
        with Session(self.engine) as session:
            return generate_chart(session, kind, output_dir=self.output)

    def assert_export(self, result):
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.minimum_required, 2)
        for name in ("svg_path", "png_path", "csv_path", "json_path"):
            path = Path(getattr(result, name))
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 0)
        stored = json.loads(Path(result.json_path).read_text())
        self.assertEqual(stored["data"], list(result.data))
        self.assertEqual(stored["excluded_counts"], result.excluded_counts)

    def latency(self, identity, turn, *, conversation="conversation", run="run", **kwargs):
        self.add(identity, "experimental_condition", {
            "status": "completed", "turn_index": turn, "conversation_id": conversation,
            "run_id": run, "provider_metadata": {"client_elapsed_latency_ms": 10 + turn}},
            status="completed", **kwargs)

    def test_recovery_native_rc_and_recovery_families_export(self):
        for family in ("rc", "recovery"):
            self.add(family, family, {"recovery_deltas": [[1, .8], [2, .3]]})
        result = self.generate("recovery_trajectory")
        self.assert_export(result)
        self.assertEqual(len(result.data), 4)
        self.assertEqual({r["record_id"] for r in result.data}, {"rc", "recovery"})

    def test_saea_exports_both_original_measurements(self):
        self.add("s", "saea", {"per_step": [
            {"position": i, "delta": .2 * i, "isolated_delta": .1, "status": "applicable"}
            for i in (1, 2)]})
        result = self.generate("saea_trajectory")
        self.assert_export(result)
        self.assertEqual([(r["delta"], r["isolated_delta"]) for r in result.data], [(.2, .1), (.4, .1)])

    def test_latency_exports_actual_client_turn_timings(self):
        self.latency("a", 0); self.latency("b", 1)
        result = self.generate("latency_per_turn")
        self.assert_export(result)
        self.assertEqual([r["latency_ms"] for r in result.data], [10, 11])

    def test_each_empty_chart_returns_insufficient_without_files(self):
        for kind in LINE_TYPES:
            result = self.generate(kind)
            self.assertEqual(result.status, "insufficient_data")
            self.assertIsNone(result.png_path)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_each_chart_rejects_short_series_without_files(self):
        self.add("r", "rc", {"recovery_deltas": [[1, .5]]})
        self.add("s", "saea", {"per_step": [
            {"position": 1, "delta": .2, "isolated_delta": .1, "status": "applicable"}]})
        self.latency("l", 0)
        for kind in LINE_TYPES:
            result = self.generate(kind)
            self.assertEqual(result.status, "insufficient_data")
            self.assertEqual(result.excluded_counts["short_series_points"], 1)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_provenance_rejects_engineering_fixtures_and_synthetic_alias(self):
        variants = [{}, {**ELIGIBLE_SHAPE, "fixture": True},
                    {**ELIGIBLE_SHAPE, "synthetic": True},
                    {**ELIGIBLE_SHAPE, "synthetic_fixture": True},
                    {**ELIGIBLE_SHAPE, "reporting_class": "engineering_only"}]
        for i, provenance in enumerate(variants):
            self.add(f"r{i}", "rc", {"recovery_deltas": [[1, .5], [2, .2]]}, provenance=provenance)
            self.add(f"s{i}", "saea", {"per_step": []}, provenance=provenance)
            self.latency(f"l{i}", i, provenance=provenance)
        for kind in LINE_TYPES:
            result = self.generate(kind)
            self.assertEqual(result.status, "insufficient_data")
            self.assertEqual(result.excluded_counts["provenance_rejected_records"], 5)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_excluded_status_counts_remain_separate(self):
        for status in ("not_applicable", "uncalibrated", "blocked"):
            self.add(status, "rc", {"recovery_deltas": [[1, .5], [2, .2]]}, status=status)
        result = self.generate("recovery_trajectory")
        self.assertEqual(result.status, "insufficient_data")
        for name in ("not_applicable_records", "uncalibrated_records", "blocked_records"):
            self.assertEqual(result.excluded_counts[name], 1)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_payload_cannot_override_blocked_record_or_hide_uncalibrated_state(self):
        self.add("a", "rc", {"status": "applicable", "recovery_deltas": [[1, .4], [2, .2]]}, status="blocked")
        self.add("b", "rc", {"status": "uncalibrated", "recovery_deltas": [[1, .4], [2, .2]]})
        result = self.generate("recovery_trajectory")
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.excluded_counts["blocked_records"], 1)
        self.assertEqual(result.excluded_counts["uncalibrated_records"], 1)

    def test_excluded_positions_are_not_bridged(self):
        self.add("s", "saea", {"per_step": [
            {"position": 1, "delta": .2, "isolated_delta": .1, "status": "applicable"},
            {"position": 2, "delta": .4, "isolated_delta": .2, "status": "uncalibrated"},
            {"position": 3, "delta": .6, "isolated_delta": .3, "status": "applicable"}]})
        figure, axis = plt.subplots()
        with patch("core.reporting.charts.plt.subplots", return_value=(figure, axis)):
            result = self.generate("saea_trajectory")
        self.assert_export(result)
        self.assertEqual(result.excluded_counts["ineligible_points"], 1)
        self.assertEqual(result.excluded_counts["uncalibrated_points"], 1)
        for line in axis.lines:
            self.assertTrue(math.isnan(line.get_ydata()[1]))
        self.assertEqual([r["position"] for r in result.data], [1, 3])

    def test_latency_does_not_join_independent_conversations(self):
        self.latency("a", 0, conversation="a")
        self.latency("b", 1, conversation="b")
        result = self.generate("latency_per_turn")
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.excluded_counts["short_series_points"], 2)

    def test_nonfinite_boolean_and_duplicate_positions_are_not_plot_points(self):
        self.add("bad", "rc", {"recovery_deltas": [[1, float("nan")], [True, .1], [2, True]]})
        self.add("duplicate", "rc", {"recovery_deltas": [[1, .4], [1, .3]]})
        result = self.generate("recovery_trajectory")
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.excluded_counts["invalid_points"], 5)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_status_counts_are_visible_even_when_provenance_also_rejects(self):
        self.add("r", "rc", {"recovery_deltas": [[1, .4], [2, .2]]},
                 status="uncalibrated", provenance={**ELIGIBLE_SHAPE, "reporting_class": "engineering_only"})
        result = self.generate("recovery_trajectory")
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.excluded_counts["provenance_rejected_records"], 1)
        self.assertEqual(result.excluded_counts["uncalibrated_records"], 1)

    def test_missing_latency_metadata_stays_unavailable(self):
        self.add("l", "experimental_condition", {"turn_index": 0, "provider_metadata": None}, status="completed")
        result = self.generate("latency_per_turn")
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.excluded_counts["invalid_points"], 1)
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
