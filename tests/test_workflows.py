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


def test_cancel_execution():
    r = client.post("/api/v1/workflows/run", json={"name": "hello", "payload": {"name": "frank"}})
    assert r.status_code == 200

    exec_id = r.json()["execution"]["id"]

    cancel_res = client.post(f"/api/v1/workflows/executions/{exec_id}/cancel")

    assert cancel_res.status_code in (200, 409)

    if cancel_res.status_code == 200:
        body = cancel_res.json()
        assert body["ok"] is True
        assert body["execution"]["state"] == "cancelled"