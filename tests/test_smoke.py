# tests/test_smoke.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_list_workflows():
    r = client.get("/api/v1/workflows")
    assert r.status_code == 200
    assert "items" in r.json()


def test_run_workflow():
    r = client.post("/api/v1/workflows/run", json={"name": "ping", "payload": {}})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["result"]["output"]["pong"] is True