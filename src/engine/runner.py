import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.models import WorkflowNode, Task, TaskNodeRun
from src.engine.context import ContextAssembler


class ClaudeCodeRunner:
    def __init__(self, context_assembler: ContextAssembler):
        self.context_assembler = context_assembler

    def run(self, task: Task, node: WorkflowNode, worktree_path: Path,
            project_name: str) -> TaskNodeRun:
        run = TaskNodeRun(
            task_id=task.id, node_id=node.id, agent_id=node.agent_id,
            status="running", started_at=datetime.now().isoformat(),
        )

        context = self.context_assembler.build_context(task, node, project_name)
        context_file = worktree_path / ".harness-context.md" if worktree_path else None
        if context_file:
            context_file.write_text(context)

        prompt = self._build_prompt(node)
        cmd = self._build_command(prompt, worktree_path, node.skill)

        try:
            result = subprocess.run(
                cmd, cwd=str(worktree_path) if worktree_path else None,
                capture_output=True, text=True, timeout=1800,
            )
            run.status = "done" if result.returncode == 0 else "failed"
            run.result_json = {
                "exit_code": result.returncode,
                "stdout_tail": result.stdout[-2000:] if result.stdout else "",
                "stderr_tail": result.stderr[-1000:] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            run.status = "failed"
            run.result_json = {"error": "timeout after 30min"}
        except Exception as e:
            run.status = "failed"
            run.result_json = {"error": str(e)}

        run.finished_at = datetime.now().isoformat()
        return run

    def _build_prompt(self, node: WorkflowNode) -> str:
        lines = []
        if "focus_path" in node.context_json:
            lines.append(f"Focus on: {node.context_json['focus_path']}")
        if "rules" in node.context_json:
            lines.append(f"Additional rules: {', '.join(node.context_json['rules'])}")
        if lines:
            lines.append("")
            lines.append("---")
            lines.append("")
        lines.append("Read the .harness-context.md file for full context and complete your assigned task.")
        return "\n".join(lines)

    def _build_command(self, prompt: str, cwd: Optional[Path], skill: str) -> list[str]:
        cmd = ["claude-code"]
        if cwd:
            cmd.extend(["--cwd", str(cwd)])
        if skill:
            cmd.extend(["--skill", skill])
        cmd.extend(["--prompt", prompt])
        return cmd
