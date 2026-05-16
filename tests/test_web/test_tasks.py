from fastapi.testclient import TestClient
from src.web.app import app
import uuid

client = TestClient(app)

def test_create_task():
    name = f"task-test-{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/projects/", json={"name": name})
    pid = resp.json()["id"]

    resp = client.post("/api/workflows/", json={
        "name": "simple", "task_type": "development", "project_id": pid,
        "nodes": [{"agent_name": "researcher"}],
    })
    assert resp.status_code == 200

    resp = client.post("/api/tasks/", json={
        "project_id": pid, "title": "implement login", "task_type": "development",
    })
    assert resp.status_code == 200
    tid = resp.json()["id"]

    resp = client.get(f"/api/tasks/{tid}")
    assert resp.status_code == 200
    assert resp.json()["task"]["title"] == "implement login"
