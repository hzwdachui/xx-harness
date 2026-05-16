import subprocess
from pathlib import Path
from src.engine.workspace import WorkspaceManager


def _setup_remote(tmp_path: Path) -> str:
    remote = tmp_path / "remote"
    remote.mkdir()
    subprocess.run(["git", "-C", str(remote), "init", "-b", "master"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(remote), "config", "user.email", "test@test"], check=True)
    subprocess.run(["git", "-C", str(remote), "config", "user.name", "test"], check=True)
    (remote / "readme.md").write_text("# test")
    subprocess.run(["git", "-C", str(remote), "add", "."], check=True)
    subprocess.run(["git", "-C", str(remote), "commit", "-m", "init"], check=True, capture_output=True)
    return str(remote)


def test_bare_clone_and_worktree(tmp_path: Path):
    remote = _setup_remote(tmp_path)
    wm = WorkspaceManager(root=tmp_path / "workspace")

    bare = wm.ensure_bare_clone("proj1", "repo1", remote)
    assert bare.exists()
    assert (bare / "HEAD").exists()

    wt = wm.create_worktree("proj1", task_id=42, repo_name="repo1", base_branch="master")
    assert wt.exists()
    assert (wt / "readme.md").exists()

    wm.remove_worktree("proj1", 42, "repo1")
    assert not wt.exists()
