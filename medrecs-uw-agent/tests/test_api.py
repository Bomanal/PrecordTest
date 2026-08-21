from medrecs_uw.api import APP
from fastapi.testclient import TestClient


def test_health_dashboard_and_run_roundtrip():
    client = TestClient(APP)
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["agents_live"] == ["BLK-REQS-CHASE", "BLK-INTAKE-MONITOR", "BLK-AUTO-ARCHIVE"]

    page = client.get("/")
    assert page.status_code == 200
    assert "Medical Records underwriting workbench" in page.text
    assert "Test agents" in page.text

    kpis = client.get("/dashboard/kpis")
    assert kpis.status_code == 200
    assert kpis.json()["cards"]

    cases = client.get("/cases/synthetic").json()["cases"]
    req = next(c for c in cases if c["underwriting_case_id"] == "UW-REQ-01")
    response = client.post("/agents/BLK-REQS-CHASE/run", json={"case": req, "stage": "s3"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["agent_id"] == "BLK-REQS-CHASE"
    assert payload["result"]["status"] == "checkpoint_pending"
    assert payload["checkpoint"]

    pending = client.get("/checkpoints").json()["pending"]
    assert pending
    resolved = client.post(
        f"/checkpoints/{pending[0]['checkpoint_run_id']}",
        json={"action": "approve", "reviewer": "underwriter"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "approved"
