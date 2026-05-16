from fastapi.testclient import TestClient
from src.web.app import app
import uuid

client = TestClient(app)


def test_create_issue():
    name = f"issue-test-{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/projects/", json={"name": name})
    pid = resp.json()["id"]

    resp = client.post("/api/issues/", json={
        "project_id": pid, "error_pattern": "agent forgets dev server setup",
        "root_cause": "no init.sh in repo",
    })
    assert resp.status_code == 200

    resp = client.get(f"/api/issues/project/{pid}")
    assert len(resp.json()) == 1


def test_create_rule():
    name = f"rule-test-{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/projects/", json={"name": name})
    pid = resp.json()["id"]

    resp = client.post("/api/issues/rules", json={
        "project_id": pid, "rule_type": "style", "content": "use snake_case",
    })
    assert resp.status_code == 200

    resp = client.get(f"/api/issues/rules/project/{pid}")
    assert len(resp.json()) == 1
