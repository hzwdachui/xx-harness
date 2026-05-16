from src.models import Task, TaskType, Project, WorkflowNode


def test_task_defaults():
    t = Task(project_id=1, title="test task")
    assert t.task_type == TaskType.DEVELOPMENT
    assert t.status == "pending"
    assert t.complexity == "medium"


def test_workflow_node_dag_deps():
    a = WorkflowNode(workflow_id=1, agent_id=1, depends_on=[2, 3], position=0)
    b = WorkflowNode(workflow_id=1, agent_id=2, depends_on=[], position=1)
    assert len(a.depends_on) == 2
    assert len(b.depends_on) == 0


def test_project_repr():
    p = Project(name="my-project", description="test")
    assert p.name == "my-project"
