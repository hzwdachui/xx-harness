from src.engine.context import ContextAssembler
from src.db.repositories import (
    ProjectRepo, KnownIssueRepo, ConstraintRuleRepo,
)
from src.models import Project, Task, WorkflowNode, KnownIssue, ConstraintRule


def test_build_tier1(tmp_db):
    proj_repo = ProjectRepo(tmp_db)
    pid = proj_repo.create(Project(name="test-project", description="test desc", boundary="src/"))

    cr_repo = ConstraintRuleRepo(tmp_db)
    cr_repo.create(ConstraintRule(rule_type="style", content="use snake_case", project_id=pid))

    asm = ContextAssembler(tmp_db)
    task = Task(project_id=pid, id=1, title="add login")

    ctx = asm.build_tier1(task, "test-project")
    assert "test-project" in ctx
    assert "add login" in ctx
    assert "snake_case" in ctx


def test_build_tier2_with_issues(tmp_db):
    proj_repo = ProjectRepo(tmp_db)
    pid = proj_repo.create(Project(name="p", description="", boundary=""))

    ki_repo = KnownIssueRepo(tmp_db)
    ki_repo.create(KnownIssue(error_pattern="circular import", root_cause="wrong module layout", project_id=pid))

    asm = ContextAssembler(tmp_db)
    task = Task(project_id=pid, id=1, title="test")
    node = WorkflowNode(workflow_id=1, agent_id=1, skill="superpowers:brainstorming", id=1)

    ctx = asm.build_tier2(task, node, agent_skills="superpowers:brainstorming, read-only access")
    assert "circular import" in ctx
    assert "superpowers:brainstorming" in ctx
