"""Contract smoke for the narrow Phase 11 surface consumed by the dashboard."""
import unittest

from fastapi.testclient import TestClient

from apps.api.main import create_app


class DashboardApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app("sqlite:///:memory:"))

    def test_dashboard_health_readiness_and_records_contract(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/ready").json(), {"status": "ready"})
        response = self.client.get("/scientific-records?limit=25&offset=0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"items", "limit", "offset"})
        self.assertEqual(response.json()["items"], [])

    def test_dashboard_pagination_validation_contract(self) -> None:
        response = self.client.get("/scientific-records?limit=0&offset=0")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"code": "invalid_pagination"})

    def test_model_scores_contract(self) -> None:
        response = self.client.get("/model-scores")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"items": [], "total": 0, "limit": 25, "offset": 0})
        self.assertEqual(self.client.get("/dashboard-summary").json()["counts"]["model-scores"], 0)

    def test_verified_calibration_summary_contract(self) -> None:
        response = self.client.get("/calibration-summary")
        self.assertEqual(response.status_code, 200)
        result = response.json()["result"]
        self.assertEqual(result["source_n"], 300)
        self.assertEqual(result["usable_n"], 295)
        self.assertAlmostEqual(result["cohen_kappa"], 0.2112609601698581)
