from src.db.repositories import (
    ProjectRepo, TaskNodeRunRepo, KnownIssueRepo, ConstraintRuleRepo,
)
from src.models import Task, WorkflowNode


class ContextAssembler:
    def __init__(self, db):
        self.project_repo = ProjectRepo(db)
        self.node_run_repo = TaskNodeRunRepo(db)
        self.known_issue_repo = KnownIssueRepo(db)
        self.constraint_rule_repo = ConstraintRuleRepo(db)

    def build_tier1(self, task: Task, project_name: str) -> str:
        project = self.project_repo.get(task.project_id)
        constraints = self.constraint_rule_repo.list_by_project(task.project_id)
        constraint_text = "\n".join(f"- [{r.rule_type}] {r.content}" for r in constraints)

        return f"""# Project: {project_name}

## Description
{project.description}

## Boundary
{project.boundary}

## Current Task
- Title: {task.title}
- Type: {task.task_type}
- Complexity: {task.complexity}
- Description: {task.description}

## Constraints
{constraint_text or "No additional constraints."}
"""

    def build_tier2(self, task: Task, node: WorkflowNode, agent_skills: str = "") -> str:
        parts = []

        prev_runs = self.node_run_repo.list_by_task(task.id)
        if prev_runs:
            parts.append("## Previous Stage Results")
            for run in prev_runs:
                parts.append(f"- Node {run.node_id}: status={run.status}")
                if run.result_json:
                    for k, v in run.result_json.items():
                        parts.append(f"  - {k}: {v}")

        issues = self.known_issue_repo.list_by_project(task.project_id)
        global_issues = self.known_issue_repo.list_global()
        all_issues = issues + global_issues
        if all_issues:
            parts.append("\n## Known Issues to Avoid")
            for issue in all_issues:
                parts.append(f"- {issue.error_pattern}: {issue.root_cause}")

        if agent_skills:
            parts.append(f"\n## Agent Skills\n{agent_skills}")

        return "\n".join(parts)

    def build_context(self, task: Task, node: WorkflowNode, project_name: str, agent_skills: str = "") -> str:
        t1 = self.build_tier1(task, project_name)
        t2 = self.build_tier2(task, node, agent_skills)
        return f"{t1}\n\n---\n\n{t2}"
