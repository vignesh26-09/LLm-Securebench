import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.main import create_app  # noqa: E402
from apps.api.resources import RESOURCES  # noqa: E402


def main():
    client = TestClient(create_app("sqlite:///:memory:"))
    health = client.get("/health")
    ready = client.get("/ready")
    review = client.post(
        "/internal/scientific-reviews",
        json={
            "review_id": "smoke",
            "claim_id": "claim",
            "evidence_bundle_id": "bundle",
            "reviewer_protocol": "smoke",
            "decision": "reviewed",
            "rationale": "explicit",
        },
    )
    print(
        {
            "service": "securellmbench",
            "api": True,
            "health": health.status_code,
            "ready": ready.status_code,
            "review": review.status_code,
            "scientific_claims_validated": False,
        }
    )
    assert health.status_code == 200
    assert ready.status_code == 200
    assert review.status_code == 201

    for resource in RESOURCES:
        response = client.get(f"/{resource}")
        assert response.status_code == 200 and "total" in response.json(), resource

    assert client.get("/dashboard-summary").json()["counts"]["scientific-reviews"] == 1
    assert client.get("/scientific-reviews/smoke").json()["decision"] == "reviewed"
    assert client.get("/scientific-records/missing").status_code == 404
    print({"read_resources_checked": len(RESOURCES), "summary": True, "detail": True})


if __name__ == "__main__":
    main()
