import subprocess
from pathlib import Path
from typing import Optional
from src.config import WORKSPACE_ROOT


class WorkspaceManager:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or WORKSPACE_ROOT

    def repo_bare_path(self, project_name: str, repo_name: str) -> Path:
        return self.root / project_name / "repos" / f"{repo_name}.git"

    def worktree_path(self, project_name: str, task_id: int, repo_name: str) -> Path:
        return self.root / project_name / "worktrees" / f"task-{task_id}" / repo_name

    def ensure_bare_clone(self, project_name: str, repo_name: str, git_url: str) -> Path:
        """Clone bare repo or fetch if it already exists."""
        bare_path = self.repo_bare_path(project_name, repo_name)
        if not bare_path.exists():
            bare_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--bare", git_url, str(bare_path)],
                check=True, capture_output=True,
            )
        else:
            subprocess.run(
                ["git", "-C", str(bare_path), "fetch", "--all"],
                check=True, capture_output=True,
            )
        return bare_path

    def create_worktree(self, project_name: str, task_id: int,
                        repo_name: str, base_branch: str = "master") -> Path:
        """Create a git worktree for a task. Fetches if bare clone exists."""
        bare_path = self.repo_bare_path(project_name, repo_name)
        wt_path = self.worktree_path(project_name, task_id, repo_name)
        if not wt_path.exists():
            branch = f"harness/task-{task_id}"
            wt_path.parent.mkdir(parents=True, exist_ok=True)
            # Fetch the bare clone first if we already have the repo URL isn't provided here.
            # Actually, ensure_bare_clone should be called first. But if already cloned, we still need to make sure remotes are up to date.
            subprocess.run(
                ["git", "-C", str(bare_path), "fetch", "--all"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(bare_path), "worktree", "add", str(wt_path), "-b", branch,
                 base_branch],
                check=True, capture_output=True,
            )
        return wt_path

    def remove_worktree(self, project_name: str, task_id: int, repo_name: str) -> None:
        bare_path = self.repo_bare_path(project_name, repo_name)
        wt_path = self.worktree_path(project_name, task_id, repo_name)
        if wt_path.exists():
            subprocess.run(
                ["git", "-C", str(bare_path), "worktree", "remove", str(wt_path), "--force"],
                check=True, capture_output=True,
            )
