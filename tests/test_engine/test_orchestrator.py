from unittest.mock import patch, MagicMock
from src.engine.orchestrator import Orchestrator
from src.db.repositories import ProjectRepo, TaskRepo, WorkflowRepo, WorkflowNodeRepo, RepositoryRepo
from src.models import Project, Task, Workflow, WorkflowNode, Repository


def setup_test_data(db):
    proj_repo = ProjectRepo(db)
    pid = proj_repo.create(Project(name="test-proj", description="", boundary=""))

    repo_repo = RepositoryRepo(db)
    repo_repo.create(Repository(project_id=pid, name="main", git_url="/tmp/fake"))

    wf_repo = WorkflowRepo(db)
    wid = wf_repo.create(Workflow(project_id=pid, name="simple", task_type="development"))

    node_repo = WorkflowNodeRepo(db)
    node_repo.create(WorkflowNode(workflow_id=wid, agent_id=1, id=1, position=0))
    node_repo.create(WorkflowNode(workflow_id=wid, agent_id=2, id=2, depends_on=[1],
                                   review_gate=True, position=1))

    task_repo = TaskRepo(db)
    tid = task_repo.create(Task(project_id=pid, task_type="development", workflow_id=wid,
                                title="test task"))

    return pid, wid, tid


@patch("src.engine.orchestrator.ClaudeCodeRunner")
@patch("src.engine.orchestrator.WorkspaceManager")
def test_orchestrator_runs_dag(mock_ws_class, mock_runner_class, tmp_db):
    pid, wid, tid = setup_test_data(tmp_db)

    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(
        status="done", id=1, node_id=1, agent_id=1, task_id=tid,
        result_json={}, started_at="2024-01-01T00:00:00", finished_at="2024-01-01T00:01:00",
    )
    mock_runner_class.return_value = mock_runner

    mock_ws = MagicMock()
    mock_ws_class.return_value = mock_ws

    orch = Orchestrator(tmp_db)
    orch.run_task(tid, trigger_source="web")

    task = orch.task_repo.get(tid)
    assert task.status == "completed"
