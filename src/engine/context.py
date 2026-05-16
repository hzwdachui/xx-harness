from src.db.repositories import (
    ProjectRepo, TaskRepo, TaskNodeRunRepo, WorkflowNodeRepo,
    KnownIssueRepo, ConstraintRuleRepo, SkillMappingRepo,
)
from src.models import Task, WorkflowNode


class ContextAssembler:
    def __init__(self, db, project_repo, task_repo, node_run_repo,
                 workflow_node_repo, known_issue_repo, constraint_rule_repo, skill_repo):
        self.db = db
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.node_run_repo = node_run_repo
        self.workflow_node_repo = workflow_node_repo
        self.known_issue_repo = known_issue_repo
        self.constraint_rule_repo = constraint_rule_repo
        self.skill_repo = skill_repo

    def build_tier1(self, task: Task, project_name: str) -> str:
        """Build session-persistent context: project info + task + constraints."""
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

    def build_tier2(self, task: Task, node: WorkflowNode) -> str:
        """Build stage-specific context: previous results + known issues + skills."""
        parts = []

        if self.node_run_repo is not None:
            prev_runs = self.node_run_repo.list_by_task(task.id)
            if prev_runs:
                parts.append("## Previous Stage Results")
                for run in prev_runs:
                    parts.append(f"- Node {run.node_id}: status={run.status}")
                    if run.result_json:
                        for k, v in run.result_json.items():
                            parts.append(f"  - {k}: {v}")

        if self.known_issue_repo is not None:
            issues = self.known_issue_repo.list_by_project(task.project_id)
            global_issues = self.known_issue_repo.list_global()
            all_issues = issues + global_issues
            if all_issues:
                parts.append("\n## Known Issues to Avoid")
                for issue in all_issues:
                    parts.append(f"- {issue.error_pattern}: {issue.root_cause}")

        if node.skill:
            parts.append(f"\n## Active Skill\nUse skill: `{node.skill}`")

        return "\n".join(parts)

    def build_context(self, task: Task, node: WorkflowNode, project_name: str) -> str:
        t1 = self.build_tier1(task, project_name)
        t2 = self.build_tier2(task, node)
        return f"{t1}\n\n---\n\n{t2}"
