"""Entry point for Claude Code dialogue — injects harness context.

Usage: python -m src.harness_claude <project_name> [task_id]
"""
import sys
from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data, migrate
from src.db.repositories import ProjectRepo, TaskRepo
from src.engine.context import ContextAssembler
from src.config import DB_PATH


def get_harness_context(project_name: str, task_id: int | None = None) -> str:
    db = SQLiteAdapter(str(DB_PATH))
    create_schema(db)
    migrate(db)
    seed_data(db)

    proj_repo = ProjectRepo(db)
    all_projects = proj_repo.list_all()
    project = next((p for p in all_projects if p.name == project_name), None)

    if not project:
        return f"# xx-harness\nNo harness config found for project '{project_name}'."

    assembler = ContextAssembler(db)
    task_repo = TaskRepo(db)

    lines = [
        "# xx-harness Context",
        f"## Project: {project.name}",
        f"Boundary: {project.boundary}",
    ]

    if task_id:
        task = task_repo.get(task_id)
        if task:
            context = assembler.build_tier1(task, project_name)
            lines.append("")
            lines.append(context.split("## Constraints")[1] if "## Constraints" in context else "")
            lines.append(f"## Active Task: {task.title}")
            lines.append(f"Type: {task.task_type} | Status: {task.status}")
            lines.append(f"Description: {task.description}")
            return "\n".join(lines)

    # No specific task — just show project context
    from src.models import Task, WorkflowNode
    dummy_task = Task(project_id=project.id, title="(no active task)", id=0)
    context = assembler.build_tier1(dummy_task, project_name)
    return "# xx-harness Context\n" + context


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.harness_claude <project_name> [task_id]")
        sys.exit(1)
    project_name = sys.argv[1]
    task_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(get_harness_context(project_name, task_id))
