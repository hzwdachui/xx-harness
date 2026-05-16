"""Entry point for Claude Code dialogue — injects harness context.

Usage: python -m src.harness_claude <project_name> [task_id]
Place output in project's CLAUDE.md or use as a hook.
"""
import sys
from pathlib import Path
from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data
from src.db.repositories import ProjectRepo, TaskRepo, KnownIssueRepo, ConstraintRuleRepo
from src.config import DB_PATH


def get_harness_context(project_name: str, task_id: int | None = None) -> str:
    db = SQLiteAdapter(str(DB_PATH))
    create_schema(db)
    seed_data(db)

    proj_repo = ProjectRepo(db)
    all_projects = proj_repo.list_all()
    project = next((p for p in all_projects if p.name == project_name), None)

    if not project:
        return f"# xx-harness\nNo harness config found for project '{project_name}'."

    lines = [
        "# xx-harness Context",
        f"## Project: {project.name}",
        f"Boundary: {project.boundary}",
        "",
    ]

    cr_repo = ConstraintRuleRepo(db)
    rules = cr_repo.list_by_project(project.id)
    if rules:
        lines.append("## Constraints")
        for r in rules:
            lines.append(f"- [{r.rule_type}] {r.content}")
        lines.append("")

    task_repo = TaskRepo(db)
    if task_id:
        task = task_repo.get(task_id)
        if task:
            lines.append(f"## Active Task: {task.title}")
            lines.append(f"Type: {task.task_type} | Status: {task.status}")
            lines.append(f"Description: {task.description}")
            lines.append("")

    ki_repo = KnownIssueRepo(db)
    issues = ki_repo.list_by_project(project.id)
    if issues:
        lines.append("## Known Issues to Avoid")
        for i in issues:
            lines.append(f"- {i.error_pattern}: {i.root_cause}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.harness_claude <project_name> [task_id]")
        sys.exit(1)
    project_name = sys.argv[1]
    task_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(get_harness_context(project_name, task_id))
