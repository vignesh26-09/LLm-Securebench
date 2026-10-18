import unittest
from fastapi.testclient import TestClient
from apps.api.main import create_app
class ApiTests(unittest.TestCase):
 def test_health_and_request_id(self):
  response=TestClient(create_app("sqlite:///:memory:")).get("/health")
  self.assertEqual(response.status_code,200);self.assertIn("X-Request-ID",response.headers)
 def test_ready(self):self.assertEqual(TestClient(create_app("sqlite:///:memory:")).get("/ready").status_code,200)
 def test_review_is_explicit_and_not_auto_validation(self):
  client=TestClient(create_app("sqlite:///:memory:"));r=client.post("/internal/scientific-reviews",json={"review_id":"r","claim_id":"c","evidence_bundle_id":"e","reviewer_protocol":"p","decision":"reviewed","rationale":"explicit review"});self.assertEqual(r.status_code,201);self.assertFalse(r.json()["claim_validated"])
if __name__=="__main__":unittest.main()
