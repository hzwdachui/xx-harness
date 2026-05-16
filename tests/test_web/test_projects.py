import uuid

from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)


def _uniq(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_create_and_list_projects():
    name = _uniq("web-test-proj")
    resp = client.post("/api/projects/", json={"name": name, "description": "test"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.get("/api/projects/")
    projects = resp.json()
    assert any(p["id"] == pid for p in projects)


def test_create_project_with_repo():
    name = _uniq("repo-test-proj")
    resp = client.post("/api/projects/", json={"name": name})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.post(f"/api/projects/{pid}/repos", json={"name": "main", "git_url": "git@github.com:test/repo.git"})
    assert resp.status_code == 200

    resp = client.get(f"/api/projects/{pid}/repos")
    assert len(resp.json()) == 1


def test_delete_project():
    name = _uniq("delete-me")
    resp = client.post("/api/projects/", json={"name": name})
    pid = resp.json()["id"]

    resp = client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 200

    resp = client.get(f"/api/projects/{pid}")
    assert resp.status_code == 404
