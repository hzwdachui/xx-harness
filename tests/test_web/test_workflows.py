from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_create_and_list_workflow():
    import uuid
    name = f"wf-test-{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/projects/", json={"name": name})
    pid = resp.json()["id"]

    resp = client.post("/api/workflows/", json={
        "name": "standard",
        "task_type": "development",
        "project_id": pid,
        "nodes": [
            {"agent_name": "researcher"},
            {"agent_name": "planner", "depends_on": [1], "review_gate": True},
        ]
    })
    assert resp.status_code == 200

    resp = client.get(f"/api/workflows/project/{pid}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert len(resp.json()[0]["nodes"]) == 2
