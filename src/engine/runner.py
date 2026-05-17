import subprocess, json as _json, os
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.models import WorkflowNode, Task, TaskNodeRun, NodeRunStatus
from src.engine.context import ContextAssembler


class ClaudeCodeRunner:
    def __init__(self, context_assembler: ContextAssembler):
        self.context_assembler = context_assembler

    def run(
        self, task: Task, node: WorkflowNode, worktree_path: Optional[Path],
        project_name: str, run: TaskNodeRun, agent_skills: str = "",
    ) -> TaskNodeRun:
        run.status = NodeRunStatus.RUNNING.value
        run.started_at = datetime.now().isoformat()

        context = self.context_assembler.build_context(task, node, project_name, agent_skills)
        context_file = worktree_path / ".harness-context.md" if worktree_path else None
        if context_file:
            context_file.write_text(context)

        prompt = self._build_prompt(node, task, agent_skills)
        cmd = self._build_command(prompt, worktree_path, node)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(worktree_path) if worktree_path else None,
                capture_output=True, text=True, timeout=1800,
                env={**os.environ, "CLAUDE_CODE_SIMPLE": "1"},
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode == 0:
                run.status = NodeRunStatus.DONE.value
            else:
                run.status = NodeRunStatus.FAILED.value

            # Try to parse structured JSON output, fall back to text
            parsed = None
            if stdout:
                try:
                    parsed = _json.loads(stdout)
                except _json.JSONDecodeError:
                    parsed = None

            run.result_json = {
                "exit_code": result.returncode,
                "output": parsed or stdout[-4000:] if stdout else "",
                "stderr": stderr[-2000:] if stderr else "",
            }
        except subprocess.TimeoutExpired:
            run.status = NodeRunStatus.FAILED.value
            run.result_json = {"error": "timeout after 30min"}
        except FileNotFoundError:
            run.status = NodeRunStatus.FAILED.value
            run.result_json = {"error": "claude CLI not found — install Claude Code"}
        except Exception as e:
            run.status = NodeRunStatus.FAILED.value
            run.result_json = {"error": str(e)}

        run.finished_at = datetime.now().isoformat()
        return run

    def _build_prompt(self, node: WorkflowNode, task: Task, agent_skills: str = "") -> str:
        ctx: dict = getattr(node, "context_json", None) or {}
        lines = [f"# Task: {task.title}", f"Description: {task.description}", ""]

        if agent_skills:
            lines.append(f"Skills: {agent_skills}")
            lines.append("")

        if "focus_path" in ctx:
            lines.append(f"Focus on: {ctx['focus_path']}")
        if "rules" in ctx:
            for r in ctx["rules"]:
                lines.append(f"- Rule: {r}")
            lines.append("")

        lines.append("## Instructions")
        lines.append("1. Read the .harness-context.md file in this directory for full context")
        lines.append("2. Complete your assigned task using the available tools")
        lines.append("3. Report what you found, changed, or decided")

        return "\n".join(lines)

    def _build_command(
        self, prompt: str, worktree_path: Optional[Path], node: WorkflowNode,
    ) -> list[str]:
        cmd = ["claude", "-p", "--model", "sonnet"]
        cmd.extend(["--allowedTools", "Bash(git:*),Read,Write,Edit,Agent,TaskCreate,TaskUpdate,TaskList"])
        if worktree_path:
            cmd.extend(["--add-dir", str(worktree_path)])
        cmd.extend(["--output-format", "json"])
        cmd.append(prompt)
        return cmd
