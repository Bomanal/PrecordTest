from secureterm_uw.api import APP
from fastapi.testclient import TestClient


def test_health_and_run_roundtrip():
    client = TestClient(APP)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["agents_live"] == ["BLK-01", "BLK-02"]

    cases = client.get("/cases/synthetic").json()["cases"]
    fast = next(c for c in cases if c["case_identifier"] == "LUW-FAST-01")
    response = client.post("/agents/BLK-01/run", json={"case": fast, "stage": "s3"})
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["agent_id"] == "BLK-01"
    assert body["result"]["status"] in {"checkpoint_pending", "escalated", "open_item"}
