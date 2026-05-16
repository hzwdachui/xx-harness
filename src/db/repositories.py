from __future__ import annotations

import json
from typing import Any

from src.db.adapter import DatabaseAdapter
from src.models import (
    AgentTemplate,
    ConstraintRule,
    KnownIssue,
    Project,
    Repository,
    SkillMapping,
    Task,
    TaskNodeRun,
    Workflow,
    WorkflowNode,
)


class ProjectRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, p: Project) -> int:
        self._db.execute(
            "INSERT INTO project (name, description, boundary) VALUES (?, ?, ?)",
            [p.name, p.description, p.boundary],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def get(self, project_id: int) -> Project | None:
        row = self._db.fetch_one("SELECT * FROM project WHERE id = ?", [project_id])
        if row is None:
            return None
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            boundary=row["boundary"],
            created_at=row["created_at"],
        )

    def list_all(self) -> list[Project]:
        rows = self._db.fetch_all("SELECT * FROM project ORDER BY id DESC")
        return [
            Project(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                boundary=r["boundary"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def update(self, p: Project) -> None:
        self._db.execute(
            "UPDATE project SET name=?, description=?, boundary=? WHERE id=?",
            [p.name, p.description, p.boundary, p.id],
        )

    def delete(self, project_id: int) -> None:
        self._db.execute("DELETE FROM project WHERE id = ?", [project_id])


class RepositoryRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, r: Repository) -> int:
        self._db.execute(
            "INSERT INTO repository (project_id, name, git_url, default_branch) VALUES (?, ?, ?, ?)",
            [r.project_id, r.name, r.git_url, r.default_branch],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[Repository]:
        rows = self._db.fetch_all(
            "SELECT * FROM repository WHERE project_id = ?", [project_id]
        )
        return [
            Repository(
                id=r["id"],
                project_id=r["project_id"],
                name=r["name"],
                git_url=r["git_url"],
                default_branch=r["default_branch"],
            )
            for r in rows
        ]

    def delete(self, repo_id: int) -> None:
        self._db.execute("DELETE FROM repository WHERE id = ?", [repo_id])


class AgentRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def list_all(self) -> list[AgentTemplate]:
        rows = self._db.fetch_all("SELECT * FROM agent_template")
        return [
            AgentTemplate(
                id=r["id"],
                name=r["name"],
                role=r["role"],
                system_prompt=r["system_prompt"],
                tools_json=r["tools_json"],
            )
            for r in rows
        ]

    def get(self, agent_id: int) -> AgentTemplate | None:
        row = self._db.fetch_one("SELECT * FROM agent_template WHERE id = ?", [agent_id])
        if row is None:
            return None
        return AgentTemplate(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            system_prompt=row["system_prompt"],
            tools_json=row["tools_json"],
        )

    def get_by_name(self, name: str) -> AgentTemplate | None:
        row = self._db.fetch_one("SELECT * FROM agent_template WHERE name = ?", [name])
        if row is None:
            return None
        return AgentTemplate(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            system_prompt=row["system_prompt"],
            tools_json=row["tools_json"],
        )


class WorkflowRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, w: Workflow) -> int:
        self._db.execute(
            "INSERT INTO workflow (project_id, name, task_type) VALUES (?, ?, ?)",
            [w.project_id, w.name, w.task_type],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[Workflow]:
        rows = self._db.fetch_all(
            "SELECT * FROM workflow WHERE project_id = ?", [project_id]
        )
        return [
            Workflow(
                id=r["id"],
                project_id=r["project_id"],
                name=r["name"],
                task_type=r["task_type"],
            )
            for r in rows
        ]

    def get(self, workflow_id: int) -> Workflow | None:
        row = self._db.fetch_one("SELECT * FROM workflow WHERE id = ?", [workflow_id])
        if row is None:
            return None
        return Workflow(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            task_type=row["task_type"],
        )

    def get_default_for_type(self, project_id: int, task_type: str) -> Workflow | None:
        row = self._db.fetch_one(
            "SELECT * FROM workflow WHERE project_id = ? AND task_type = ? LIMIT 1",
            [project_id, task_type],
        )
        if row is None:
            return None
        return Workflow(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            task_type=row["task_type"],
        )

    def delete(self, workflow_id: int) -> None:
        self._db.execute("DELETE FROM workflow_node WHERE workflow_id = ?", [workflow_id])
        self._db.execute("DELETE FROM workflow WHERE id = ?", [workflow_id])


class WorkflowNodeRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, node: WorkflowNode) -> int:
        self._db.execute(
            "INSERT INTO workflow_node "
            "(workflow_id, agent_id, depends_on, review_gate, skill, skill_args, context_json, position) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                node.workflow_id,
                node.agent_id,
                json.dumps(node.depends_on),
                1 if node.review_gate else 0,
                node.skill,
                node.skill_args,
                json.dumps(node.context_json),
                node.position,
            ],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def list_by_workflow(self, workflow_id: int) -> list[WorkflowNode]:
        rows = self._db.fetch_all(
            "SELECT * FROM workflow_node WHERE workflow_id = ? ORDER BY position",
            [workflow_id],
        )
        return [
            WorkflowNode(
                id=r["id"],
                workflow_id=r["workflow_id"],
                agent_id=r["agent_id"],
                depends_on=json.loads(r["depends_on"]),
                review_gate=bool(r["review_gate"]),
                skill=r["skill"],
                skill_args=r["skill_args"],
                context_json=json.loads(r["context_json"]),
                position=r["position"],
            )
            for r in rows
        ]


class TaskRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, t: Task) -> int:
        self._db.execute(
            "INSERT INTO task (project_id, task_type, workflow_id, title, description, status, complexity) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [t.project_id, t.task_type, t.workflow_id, t.title, t.description, t.status, t.complexity],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def get(self, task_id: int) -> Task | None:
        row = self._db.fetch_one("SELECT * FROM task WHERE id = ?", [task_id])
        if row is None:
            return None
        return self._row_to_task(row)

    def list_by_project(self, project_id: int, status: str | None = None) -> list[Task]:
        if status is not None:
            rows = self._db.fetch_all(
                "SELECT * FROM task WHERE project_id = ? AND status = ?",
                [project_id, status],
            )
        else:
            rows = self._db.fetch_all(
                "SELECT * FROM task WHERE project_id = ?", [project_id]
            )
        return [self._row_to_task(r) for r in rows]

    def list_pending(self) -> list[Task]:
        rows = self._db.fetch_all("SELECT * FROM task WHERE status = 'pending'")
        return [self._row_to_task(r) for r in rows]

    def update_status(self, task_id: int, status: str) -> None:
        self._db.execute("UPDATE task SET status = ? WHERE id = ?", [status, task_id])

    def update(self, t: Task) -> None:
        self._db.execute(
            "UPDATE task SET project_id=?, task_type=?, workflow_id=?, title=?, "
            "description=?, status=?, complexity=? WHERE id=?",
            [
                t.project_id,
                t.task_type,
                t.workflow_id,
                t.title,
                t.description,
                t.status,
                t.complexity,
                t.id,
            ],
        )

    def _row_to_task(self, row: dict) -> Task:
        return Task(
            id=row["id"],
            project_id=row["project_id"],
            task_type=row["task_type"],
            workflow_id=row["workflow_id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            complexity=row["complexity"],
            created_at=row["created_at"],
        )


class TaskNodeRunRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, run: TaskNodeRun) -> int:
        self._db.execute(
            "INSERT INTO task_node_run (task_id, node_id, agent_id, status, result_json, started_at, finished_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                run.task_id,
                run.node_id,
                run.agent_id,
                run.status,
                json.dumps(run.result_json),
                run.started_at,
                run.finished_at,
            ],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def update(self, run: TaskNodeRun) -> None:
        self._db.execute(
            "UPDATE task_node_run SET task_id=?, node_id=?, agent_id=?, status=?, "
            "result_json=?, started_at=?, finished_at=? WHERE id=?",
            [
                run.task_id,
                run.node_id,
                run.agent_id,
                run.status,
                json.dumps(run.result_json),
                run.started_at,
                run.finished_at,
                run.id,
            ],
        )

    def list_by_task(self, task_id: int) -> list[TaskNodeRun]:
        rows = self._db.fetch_all(
            "SELECT * FROM task_node_run WHERE task_id = ?", [task_id]
        )
        return [
            TaskNodeRun(
                id=r["id"],
                task_id=r["task_id"],
                node_id=r["node_id"],
                agent_id=r["agent_id"],
                status=r["status"],
                result_json=json.loads(r["result_json"]),
                started_at=r["started_at"],
                finished_at=r["finished_at"],
            )
            for r in rows
        ]


class KnownIssueRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, issue: KnownIssue) -> int:
        self._db.execute(
            "INSERT INTO known_issue (project_id, error_pattern, root_cause, rule_update, level) "
            "VALUES (?, ?, ?, ?, ?)",
            [issue.project_id, issue.error_pattern, issue.root_cause, issue.rule_update, issue.level],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[KnownIssue]:
        rows = self._db.fetch_all(
            "SELECT * FROM known_issue WHERE project_id = ?", [project_id]
        )
        return [self._row_to_issue(r) for r in rows]

    def list_global(self) -> list[KnownIssue]:
        rows = self._db.fetch_all(
            "SELECT * FROM known_issue WHERE level = 'global' AND project_id IS NULL"
        )
        return [self._row_to_issue(r) for r in rows]

    def _row_to_issue(self, row: dict) -> KnownIssue:
        return KnownIssue(
            id=row["id"],
            project_id=row["project_id"],
            error_pattern=row["error_pattern"],
            root_cause=row["root_cause"],
            rule_update=row["rule_update"],
            level=row["level"],
            created_at=row["created_at"],
        )


class ConstraintRuleRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def create(self, rule: ConstraintRule) -> int:
        self._db.execute(
            "INSERT INTO constraint_rule (project_id, rule_type, content, level) VALUES (?, ?, ?, ?)",
            [rule.project_id, rule.rule_type, rule.content, rule.level],
        )
        row = self._db.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[ConstraintRule]:
        rows = self._db.fetch_all(
            "SELECT * FROM constraint_rule "
            "WHERE (project_id = ?) OR (level = 'global' AND project_id IS NULL)",
            [project_id],
        )
        return [
            ConstraintRule(
                id=r["id"],
                project_id=r["project_id"],
                rule_type=r["rule_type"],
                content=r["content"],
                level=r["level"],
                created_at=r["created_at"],
            )
            for r in rows
        ]


class SkillMappingRepo:
    def __init__(self, db: DatabaseAdapter) -> None:
        self._db = db

    def get_for_role(self, agent_role: str, project_id: int | None = None) -> list[SkillMapping]:
        if project_id is not None:
            rows = self._db.fetch_all(
                "SELECT * FROM skill_mapping WHERE agent_role = ? AND project_id = ?",
                [agent_role, project_id],
            )
            if rows:
                return [
                    SkillMapping(
                        id=r["id"],
                        agent_role=r["agent_role"],
                        skill=r["skill"],
                        project_id=r["project_id"],
                    )
                    for r in rows
                ]
        rows = self._db.fetch_all(
            "SELECT * FROM skill_mapping WHERE agent_role = ? AND project_id IS NULL",
            [agent_role],
        )
        return [
            SkillMapping(
                id=r["id"],
                agent_role=r["agent_role"],
                skill=r["skill"],
                project_id=r["project_id"],
            )
            for r in rows
        ]
