from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_run_and_history():
    r = client.post("/api/v1/workflows/run", json={"name": "ping", "payload": {}})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    exec_id = data["execution"]["id"]

    r2 = client.get("/api/v1/workflows/executions")
    assert r2.status_code == 200
    assert any(x["id"] == exec_id for x in r2.json()["items"])

    r3 = client.get(f"/api/v1/workflows/executions/{exec_id}")
    assert r3.status_code == 200
    assert r3.json()["id"] == exec_id