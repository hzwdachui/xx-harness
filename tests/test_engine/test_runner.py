from unittest.mock import patch, MagicMock
from pathlib import Path
from src.engine.runner import ClaudeCodeRunner
from src.engine.context import ContextAssembler
from src.models import Task, WorkflowNode


@patch("src.engine.runner.subprocess.run")
def test_runner_success(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
    asm = MagicMock(spec=ContextAssembler)
    asm.build_context.return_value = "# context"
    runner = ClaudeCodeRunner(asm)

    task = Task(project_id=1, id=10, title="test")
    node = WorkflowNode(workflow_id=1, agent_id=2,
                        skill="superpowers:brainstorming", id=3,
                        context_json={"focus_path": "src/auth/"})
    wt = tmp_path / "worktree"
    wt.mkdir()

    run = runner.run(task, node, wt, "test-project")
    assert run.status == "done"
    assert run.result_json["exit_code"] == 0

    context_file = wt / ".harness-context.md"
    assert context_file.exists()


@patch("src.engine.runner.subprocess.run")
def test_runner_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
    asm = MagicMock(spec=ContextAssembler)
    asm.build_context.return_value = ""
    runner = ClaudeCodeRunner(asm)

    task = Task(project_id=1, id=10, title="test")
    node = WorkflowNode(workflow_id=1, agent_id=2, id=3)
    wt = tmp_path / "worktree"
    wt.mkdir()

    run = runner.run(task, node, wt, "proj")
    assert run.status == "failed"
