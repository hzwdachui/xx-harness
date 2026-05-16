from src.db.repositories import ProjectRepo, RepositoryRepo, TaskRepo, KnownIssueRepo
from src.models import Project, Repository, Task, KnownIssue


def test_project_crud(tmp_db):
    repo = ProjectRepo(tmp_db)
    pid = repo.create(Project(name="test-proj", description="desc"))
    assert pid > 0
    p = repo.get(pid)
    assert p.name == "test-proj"
    p.description = "updated"
    repo.update(p)
    assert repo.get(pid).description == "updated"
    assert len(repo.list_all()) == 1


def test_task_create_and_update(tmp_db):
    # Create a project first for FK constraint
    prepo = ProjectRepo(tmp_db)
    pid = prepo.create(Project(name="test-proj-for-task", description="desc"))

    repo = TaskRepo(tmp_db)
    tid = repo.create(Task(project_id=pid, title="implement login", task_type="development"))
    t = repo.get(tid)
    assert t.status == "pending"
    repo.update_status(tid, "running")
    assert repo.get(tid).status == "running"


def test_known_issue_create(tmp_db):
    # Create a project first for FK constraint
    prepo = ProjectRepo(tmp_db)
    pid = prepo.create(Project(name="test-proj-for-issue", description="desc"))

    repo = KnownIssueRepo(tmp_db)
    repo.create(KnownIssue(error_pattern="context overflow", root_cause="too much input", project_id=pid))
    issues = repo.list_by_project(pid)
    assert len(issues) == 1
    assert issues[0].error_pattern == "context overflow"
