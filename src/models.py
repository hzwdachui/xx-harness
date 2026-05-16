from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    EXPLORATION = "exploration"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PLAN_READY = "plan_ready"
    PLAN_APPROVED = "plan_approved"
    EXECUTING = "executing"
    CODE_REVIEW = "code_review"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    WAITING_REVIEW = "waiting_review"


class RuleLevel(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"


@dataclass
class Project:
    name: str
    description: str = ""
    boundary: str = ""
    id: int | None = None
    created_at: str | None = None


@dataclass
class Repository:
    project_id: int
    name: str
    git_url: str
    default_branch: str = "master"
    id: int | None = None


@dataclass
class AgentTemplate:
    name: str
    role: str
    system_prompt: str = ""
    tools_json: str = "[]"
    id: int | None = None


@dataclass
class Workflow:
    project_id: int
    name: str
    task_type: str = "custom"
    id: int | None = None


@dataclass
class WorkflowNode:
    workflow_id: int
    agent_id: int
    depends_on: list[int] = field(default_factory=list)
    review_gate: bool = False
    skill: str = ""
    skill_args: str = ""
    context_json: dict[str, Any] = field(default_factory=dict)
    position: int = 0
    id: int | None = None


@dataclass
class Task:
    project_id: int
    title: str
    task_type: str = "development"
    description: str = ""
    status: str = "pending"
    complexity: str = "medium"
    workflow_id: int | None = None
    id: int | None = None
    created_at: str | None = None


@dataclass
class TaskNodeRun:
    task_id: int
    node_id: int
    agent_id: int
    status: str = "pending"
    result_json: dict[str, Any] = field(default_factory=dict)
    id: int | None = None
    started_at: str | None = None
    finished_at: str | None = None


@dataclass
class AgentSession:
    task_id: int
    node_run_id: int | None = None
    session_log: str = ""
    summary: str = ""
    id: int | None = None
    created_at: str | None = None


@dataclass
class KnownIssue:
    error_pattern: str
    root_cause: str = ""
    rule_update: str = ""
    level: str = "project"
    project_id: int | None = None
    id: int | None = None
    created_at: str | None = None


@dataclass
class ConstraintRule:
    rule_type: str
    content: str
    level: str = "project"
    project_id: int | None = None
    id: int | None = None
    created_at: str | None = None


@dataclass
class SkillMapping:
    agent_role: str
    skill: str
    project_id: int | None = None
    id: int | None = None
