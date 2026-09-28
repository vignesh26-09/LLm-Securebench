import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy.orm import Session

from core.persistence.database import Base, make_engine
from core.persistence.models import ScientificRecordEntity
from core.reporting.charts import generate_chart
from core.reporting.imports import import_persisted_judge_calibration


ROOT = Path(__file__).resolve().parents[1]
REAL = {"data_origin": "real_persisted", "reporting_class": "phase1_scientific",
        "fixture": False, "synthetic": False, "model": "model-a"}


class ReportingChartTests(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _add(self, family, status, payload, identifier):
        with Session(self.engine) as session:
            session.add(ScientificRecordEntity(id=identifier, family=family, schema_version="test-v1",
                scope="TEST", owner_id="model-a", status=status, payload=payload, provenance=REAL))
            session.commit()

    def _generate(self, chart_type):
        with Session(self.engine) as session:
            return generate_chart(session, chart_type, output_dir=self.output)

    def _assert_export(self, result):
        self.assertEqual(result.status, "ready")
        for path in (result.svg_path, result.png_path, result.csv_path, result.json_path):
            self.assertTrue(Path(path).is_file())
        self.assertEqual(json.loads(Path(result.json_path).read_text(encoding="utf-8"))["data"], list(result.data))

    def test_judge_calibration_uses_actual_stored_300_record_artifact(self):
        with Session(self.engine) as session:
            self.assertTrue(import_persisted_judge_calibration(session,
                ROOT / "experiments" / "jailbreakbench-validation" / "calibration_artifact_v1.json"))
        result = self._generate("judge_calibration")
        self._assert_export(result)
        row = result.data[0]
        self.assertEqual({key: row[key] for key in ("tp", "fp", "fn", "tn")},
                         {"tp": 108, "fp": 135, "fn": 1, "tn": 51})
        self.assertEqual(row["source_n"], 300)
        self.assertEqual(row["usable_n"], 295)
        self.assertEqual(row["coverage"], 0.9833333333333333)
        self.assertEqual(row["raw_agreement"], 0.5389830508474577)
        self.assertEqual(row["cohen_kappa"], 0.2112609601698581)

    def test_bsda_distribution_exports_real_shaped_records(self):
        for index in range(5):
            self._add("bsda", "computed", {"components": {"D_sem": .1 + index, "D_safety": .2,
                "D_instr": .3, "D_struct": .4}}, f"b{index}")
        result = self._generate("bsda_distribution")
        self._assert_export(result)
        self.assertEqual(result.record_count, 5)
        self.assertEqual(result.data[0]["component"], "D_sem")

    def test_recovery_distribution_excludes_non_applicable_records(self):
        for index in range(5): self._add("recovery", "applicable", {"rc_auc_raw": .1 + index}, f"r{index}")
        self._add("recovery", "not_applicable", {"rc_auc_raw": 0}, "r-na")
        result = self._generate("recovery_distribution")
        self._assert_export(result)
        self.assertEqual(result.record_count, 6)
        self.assertEqual(result.excluded_counts["not_applicable"], 1)

    def test_saea_deviation_exports_applicable_deltas_only(self):
        for index in range(5):
            self._add("saea", "computed", {"per_step": [{"position": index + 1, "status": "applicable",
                "delta": .5, "isolated_delta": .2}]}, f"s{index}")
        self._add("saea", "undefined", {"per_step": [{"position": 1, "status": "undefined",
            "delta": None, "isolated_delta": None}]}, "s-blocked")
        result = self._generate("saea_deviation")
        self._assert_export(result)
        self.assertEqual(result.record_count, 6)
        self.assertEqual(result.excluded_counts["undefined_or_blocked"], 1)

    def test_applicability_summary_exports_real_status_counts(self):
        self._add("bsda", "computed", {"model": "model-a"}, "a1")
        self._add("recovery", "not_applicable", {"model": "model-a"}, "a2")
        result = self._generate("applicability_summary")
        self._assert_export(result)
        self.assertEqual({(row["metric"], row["status"]): row["count"] for row in result.data},
                         {("bsda", "computed"): 1, ("recovery", "not_applicable"): 1})

    def test_engineering_real_data_without_reporting_class_is_not_chart_eligible(self):
        with Session(self.engine) as session:
            session.add(ScientificRecordEntity(id="engineering", family="bsda", schema_version="test-v1",
                scope="ENGINEERING", owner_id="model-a", status="computed",
                payload={"components": {"D_sem": .1, "D_safety": .2, "D_instr": .3, "D_struct": .4}},
                provenance={"data_origin": "real_persisted", "fixture": False, "synthetic": False,
                            "reporting_class": "engineering"}))
            session.commit()
        result = self._generate("bsda_distribution")
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(result.record_count, 0)
        self.assertIsNone(result.svg_path)

    def test_each_chart_refuses_near_empty_data_without_writing_images(self):
        for chart_type in ("judge_calibration", "bsda_distribution", "recovery_distribution",
                           "saea_deviation", "applicability_summary"):
            with self.subTest(chart_type=chart_type):
                result = self._generate(chart_type)
                self.assertEqual(result.status, "insufficient_data")
                self.assertIsNone(result.svg_path)
                self.assertEqual(list(self.output.glob("*.svg")), [])


if __name__ == "__main__":
    unittest.main()
