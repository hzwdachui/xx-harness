# xx-harness MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the xx-harness framework MVP — a Python orchestration engine + FastAPI web backend + React frontend that manages Claude Code-powered development tasks with DAG workflows, git worktree isolation, and skill integration.

**Architecture:** Python monolith with clear module boundaries — `db/` (data layer with adapter pattern), `engine/` (DAG orchestration, workspace, context, Claude Code runner), `web/` (FastAPI routes + WebSocket). SQLite via adapter for MVP. React SPA frontend. Both Claude Code dialogue and Web UI trigger the same orchestration engine.

**Tech Stack:** Python 3.12+, FastAPI, SQLite (via adapter), React 18 + TypeScript, git worktree, Claude Code CLI

---

## File Structure

```
xx-harness/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── config.py                  # Config from env/file
│   ├── db/
│   │   ├── __init__.py
│   │   ├── adapter.py             # Abstract DAO interfaces
│   │   ├── sqlite.py              # SQLite implementation
│   │   └── schema.py              # DDL + seed data
│   ├── models.py                  # All dataclasses
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── workspace.py           # Git bare clone + worktree
│   │   ├── dag.py                 # DAG parser + scheduler
│   │   ├── context.py             # 3-tier context assembler
│   │   ├── runner.py              # Claude Code process launcher
│   │   └── orchestrator.py        # Main orchestrator
│   ├── web/
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI app factory
│   │   ├── deps.py                # Dependency injection
│   │   ├── routes/
│   │   │   ├── projects.py
│   │   │   ├── workflows.py
│   │   │   ├── agents.py
│   │   │   ├── tasks.py
│   │   │   └── issues.py
│   │   └── ws.py                  # WebSocket trace endpoint
│   └── seed.py                    # Default agent templates + workflows + skill mappings
├── tests/
│   ├── conftest.py
│   ├── test_db/
│   │   ├── test_adapter.py
│   │   └── test_sqlite.py
│   ├── test_engine/
│   │   ├── test_workspace.py
│   │   ├── test_dag.py
│   │   ├── test_context.py
│   │   └── test_runner.py
│   └── test_web/
│       ├── test_projects.py
│       ├── test_workflows.py
│       └── test_tasks.py
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api.ts
        ├── pages/
        │   ├── ProjectList.tsx
        │   ├── ProjectDetail.tsx
        │   ├── WorkflowEditor.tsx
        │   ├── TaskCreate.tsx
        │   └── TaskTrace.tsx
        └── components/
            ├── Layout.tsx
            ├── DAGView.tsx
            └── StatusBadge.tsx
```

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `tests/conftest.py`
- Create: `.gitignore` (add entry for `workspace/`)

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "xx-harness"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "websockets>=14",
    "pydantic>=2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.25",
    "httpx>=0.28",
]
```

- [ ] **Step 2: Create src/config.py**

```python
import os
from pathlib import Path

HARNESS_HOME = Path(os.environ.get("XX_HARNESS_HOME", Path.home() / ".xx-harness"))
DB_PATH = HARNESS_HOME / "harness.db"
WORKSPACE_ROOT = HARNESS_HOME / "workspace"
WEB_PORT = int(os.environ.get("XX_HARNESS_PORT", "8720"))

HARNESS_HOME.mkdir(parents=True, exist_ok=True)
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 3: Create tests/conftest.py**

```python
import pytest
import tempfile
from pathlib import Path
from src.db.adapter import DatabaseAdapter
from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data

@pytest.fixture
def tmp_db() -> DatabaseAdapter:
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        adapter = SQLiteAdapter(str(db_path))
        create_schema(adapter)
        seed_data(adapter)
        yield adapter

@pytest.fixture
def tmp_workspace() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
```

- [ ] **Step 4: Run test to confirm setup works**

```bash
python -c "from src.config import HARNESS_HOME, DB_PATH; print(f'HARNESS_HOME={HARNESS_HOME}')"
```
Expected: Prints path without error.

- [ ] **Step 5: Install dependencies and commit**

```bash
pip install -e ".[dev]"
git add pyproject.toml src/__init__.py src/config.py tests/conftest.py .gitignore
git commit -m "feat: project scaffolding with config and test fixtures"
```

---

### Task 2: Data layer — adapter interface

**Files:**
- Create: `src/db/__init__.py`
- Create: `src/db/adapter.py`
- Test: `tests/test_db/test_adapter.py` (contract test, will be run against SQLite in Task 3)

- [ ] **Step 1: Write failing contract test in tests/test_db/test_adapter.py**

```python
"""Contract test for DatabaseAdapter — run against any adapter implementation."""
import pytest
from src.db.adapter import DatabaseAdapter

def test_adapter_execute_and_fetch(tmp_db: DatabaseAdapter):
    tmp_db.execute("CREATE TABLE _test (id INTEGER PRIMARY KEY, name TEXT)")
    tmp_db.execute("INSERT INTO _test (name) VALUES (?)", ["alice"])
    rows = tmp_db.fetch_all("SELECT * FROM _test")
    assert len(rows) == 1
    assert rows[0]["name"] == "alice"

def test_adapter_transaction_commit(tmp_db: DatabaseAdapter):
    tmp_db.execute("CREATE TABLE _test2 (val TEXT)")
    with tmp_db.transaction():
        tmp_db.execute("INSERT INTO _test2 (val) VALUES (?)", ["x"])
    rows = tmp_db.fetch_all("SELECT * FROM _test2")
    assert len(rows) == 1

def test_adapter_transaction_rollback(tmp_db: DatabaseAdapter):
    tmp_db.execute("CREATE TABLE _test3 (val TEXT)")
    try:
        with tmp_db.transaction():
            tmp_db.execute("INSERT INTO _test3 (val) VALUES (?)", ["y"])
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    rows = tmp_db.fetch_all("SELECT * FROM _test3")
    assert len(rows) == 0
```

- [ ] **Step 2: Create src/db/adapter.py**

```python
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any

class DatabaseAdapter(ABC):
    @abstractmethod
    def execute(self, sql: str, params: list[Any] | None = None) -> None: ...
    @abstractmethod
    def fetch_all(self, sql: str, params: list[Any] | None = None) -> list[dict]: ...
    @abstractmethod
    def fetch_one(self, sql: str, params: list[Any] | None = None) -> dict | None: ...

    @abstractmethod
    @contextmanager
    def transaction(self): ...
```

- [ ] **Step 3: Commit**

```bash
git add src/db/__init__.py src/db/adapter.py tests/test_db/test_adapter.py
git commit -m "feat: database adapter abstract interface with contract test"
```

---

### Task 3: Data layer — SQLite adapter + schema

**Files:**
- Create: `src/db/sqlite.py`
- Create: `src/db/schema.py`
- Test: `tests/test_db/test_sqlite.py`

- [ ] **Step 1: Create src/db/sqlite.py**

```python
import sqlite3
from contextlib import contextmanager
from typing import Any
from src.db.adapter import DatabaseAdapter

class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def execute(self, sql: str, params: list[Any] | None = None) -> None:
        self._conn.execute(sql, params or [])

    def fetch_all(self, sql: str, params: list[Any] | None = None) -> list[dict]:
        cur = self._conn.execute(sql, params or [])
        return [dict(row) for row in cur.fetchall()]

    def fetch_one(self, sql: str, params: list[Any] | None = None) -> dict | None:
        cur = self._conn.execute(sql, params or [])
        row = cur.fetchone()
        return dict(row) if row else None

    @contextmanager
    def transaction(self):
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
```

- [ ] **Step 2: Create src/db/schema.py**

```python
from src.db.adapter import DatabaseAdapter

def create_schema(db: DatabaseAdapter) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS project (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            boundary TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS repository (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES project(id),
            name TEXT NOT NULL,
            git_url TEXT NOT NULL,
            default_branch TEXT DEFAULT 'master'
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS agent_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            system_prompt TEXT DEFAULT '',
            tools_json TEXT DEFAULT '[]'
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS workflow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES project(id),
            name TEXT NOT NULL,
            task_type TEXT DEFAULT 'custom'
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS workflow_node (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL REFERENCES workflow(id),
            agent_id INTEGER NOT NULL REFERENCES agent_template(id),
            depends_on TEXT DEFAULT '[]',
            review_gate INTEGER DEFAULT 0,
            skill TEXT DEFAULT '',
            skill_args TEXT DEFAULT '',
            context_json TEXT DEFAULT '{}',
            position INTEGER DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES project(id),
            task_type TEXT NOT NULL DEFAULT 'development',
            workflow_id INTEGER REFERENCES workflow(id),
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            complexity TEXT DEFAULT 'medium',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS task_node_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES task(id),
            node_id INTEGER NOT NULL REFERENCES workflow_node(id),
            agent_id INTEGER NOT NULL REFERENCES agent_template(id),
            status TEXT DEFAULT 'pending',
            result_json TEXT DEFAULT '{}',
            started_at TEXT,
            finished_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS agent_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES task(id),
            node_run_id INTEGER REFERENCES task_node_run(id),
            session_log TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS known_issue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES project(id),
            error_pattern TEXT NOT NULL,
            root_cause TEXT DEFAULT '',
            rule_update TEXT DEFAULT '',
            level TEXT DEFAULT 'project',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS constraint_rule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES project(id),
            rule_type TEXT NOT NULL,
            content TEXT NOT NULL,
            level TEXT DEFAULT 'project',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS skill_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_role TEXT NOT NULL,
            skill TEXT NOT NULL,
            project_id INTEGER REFERENCES project(id),
            UNIQUE(agent_role, project_id)
        )
    """)

def seed_data(db: DatabaseAdapter) -> None:
    agents = [
        ("researcher", "研究员", "探索代码库，分析结构，输出调研报告。你只有只读权限。"),
        ("planner", "规划师", "基于需求和调研，产出结构化执行计划。你有只读权限和写计划权限。"),
        ("executor", "执行者", "按计划实现功能，遵循所有约束规则。你有读写和 git 权限。"),
        ("reviewer", "审查者", "审查代码变更，跑 Linter 和测试，输出问题清单。你有只读权限。"),
        ("tester", "测试者", "编写和运行测试，验证功能正确性。你有读写权限。"),
    ]
    for name, role, prompt in agents:
        existing = db.fetch_one("SELECT id FROM agent_template WHERE name=?", [name])
        if not existing:
            db.execute(
                "INSERT INTO agent_template (name, role, system_prompt) VALUES (?, ?, ?)",
                [name, role, prompt],
            )

    skills = [
        ("planner", "superpowers:brainstorming"),
        ("planner", "superpowers:writing-plans"),
        ("executor", "superpowers:test-driven-development"),
        ("executor", "superpowers:subagent-driven-development"),
        ("reviewer", "superpowers:systematic-debugging"),
        ("reviewer", "superpowers:verification-before-completion"),
    ]
    for role, skill in skills:
        existing = db.fetch_one("SELECT id FROM skill_mapping WHERE agent_role=? AND skill=?", [role, skill])
        if not existing:
            db.execute("INSERT INTO skill_mapping (agent_role, skill) VALUES (?, ?)", [role, skill])
```

- [ ] **Step 3: Run contract tests against SQLite**

```bash
pytest tests/test_db/test_adapter.py -v
```
Expected: 3 tests PASS.

- [ ] **Step 4: Create tests/test_db/test_sqlite.py**

```python
from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data

def test_schema_creation(tmp_path):
    db = SQLiteAdapter(str(tmp_path / "test.db"))
    create_schema(db)
    tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    table_names = [t["name"] for t in tables]
    assert "project" in table_names
    assert "task" in table_names
    assert "workflow_node" in table_names
    assert "known_issue" in table_names
    assert "skill_mapping" in table_names

def test_seed_data(tmp_path):
    db = SQLiteAdapter(str(tmp_path / "test.db"))
    create_schema(db)
    seed_data(db)
    agents = db.fetch_all("SELECT name FROM agent_template")
    assert len(agents) == 5
    skills = db.fetch_all("SELECT * FROM skill_mapping")
    assert len(skills) >= 6
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_db/ -v
```
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add src/db/sqlite.py src/db/schema.py tests/test_db/test_sqlite.py
git commit -m "feat: SQLite adapter with schema migration and seed data"
```

---

### Task 4: Core models (dataclasses)

**Files:**
- Create: `src/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Create src/models.py**

```python
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
```

- [ ] **Step 2: Create tests/test_models.py**

```python
from src.models import Task, TaskType, Project, WorkflowNode

def test_task_defaults():
    t = Task(project_id=1, title="test task")
    assert t.task_type == TaskType.DEVELOPMENT
    assert t.status == "pending"
    assert t.complexity == "medium"

def test_workflow_node_dag_deps():
    a = WorkflowNode(workflow_id=1, agent_id=1, depends_on=[2, 3], position=0)
    b = WorkflowNode(workflow_id=1, agent_id=2, depends_on=[], position=1)
    assert len(a.depends_on) == 2
    assert len(b.depends_on) == 0

def test_project_repr():
    p = Project(name="my-project", description="test")
    assert p.name == "my-project"
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_models.py -v
```
Expected: 3 PASS.

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: core data model dataclasses"
```

---

### Task 5: Project and repository repositories (data access)

**Files:**
- Modify: `src/db/adapter.py` (add repository methods)
- Create: `src/db/repositories.py`
- Test: `tests/test_db/test_repositories.py`

Wait, let me restructure. Rather than putting methods on the adapter, let me create concrete repository classes that take the adapter.

Actually, let me keep it simple. The adapter stays as a raw SQL interface. I'll build repository functions/classes on top.

Let me reconsider the file structure. For MVP, I'll put all repository logic in `src/db/repositories.py` with functions that take a `DatabaseAdapter`.

- [ ] **Step 1: Create src/db/repositories.py — ProjectRepo**

```python
from src.db.adapter import DatabaseAdapter
from src.models import Project, Repository, AgentTemplate, Workflow, WorkflowNode, Task, TaskNodeRun, KnownIssue, ConstraintRule, SkillMapping

class ProjectRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, p: Project) -> int:
        self.db.execute(
            "INSERT INTO project (name, description, boundary) VALUES (?, ?, ?)",
            [p.name, p.description, p.boundary],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def get(self, project_id: int) -> Project | None:
        row = self.db.fetch_one("SELECT * FROM project WHERE id=?", [project_id])
        return Project(**row) if row else None

    def list_all(self) -> list[Project]:
        return [Project(**r) for r in self.db.fetch_all("SELECT * FROM project ORDER BY id DESC")]

    def update(self, p: Project) -> None:
        self.db.execute(
            "UPDATE project SET name=?, description=?, boundary=? WHERE id=?",
            [p.name, p.description, p.boundary, p.id],
        )

    def delete(self, project_id: int) -> None:
        self.db.execute("DELETE FROM project WHERE id=?", [project_id])
```

- [ ] **Step 2: Add RepositoryRepo to src/db/repositories.py**

```python
class RepositoryRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, r: Repository) -> int:
        self.db.execute(
            "INSERT INTO repository (project_id, name, git_url, default_branch) VALUES (?, ?, ?, ?)",
            [r.project_id, r.name, r.git_url, r.default_branch],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[Repository]:
        return [Repository(**r) for r in self.db.fetch_all(
            "SELECT * FROM repository WHERE project_id=? ORDER BY name", [project_id]
        )]

    def delete(self, repo_id: int) -> None:
        self.db.execute("DELETE FROM repository WHERE id=?", [repo_id])
```

- [ ] **Step 3: Add AgentRepo, WorkflowRepo, WorkflowNodeRepo**

```python
class AgentRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def list_all(self) -> list[AgentTemplate]:
        return [AgentTemplate(**r) for r in self.db.fetch_all("SELECT * FROM agent_template")]

    def get(self, agent_id: int) -> AgentTemplate | None:
        row = self.db.fetch_one("SELECT * FROM agent_template WHERE id=?", [agent_id])
        return AgentTemplate(**row) if row else None

    def get_by_name(self, name: str) -> AgentTemplate | None:
        row = self.db.fetch_one("SELECT * FROM agent_template WHERE name=?", [name])
        return AgentTemplate(**row) if row else None


class WorkflowRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, w: Workflow) -> int:
        self.db.execute(
            "INSERT INTO workflow (project_id, name, task_type) VALUES (?, ?, ?)",
            [w.project_id, w.name, w.task_type],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[Workflow]:
        return [Workflow(**r) for r in self.db.fetch_all(
            "SELECT * FROM workflow WHERE project_id=? ORDER BY name", [project_id]
        )]

    def get(self, workflow_id: int) -> Workflow | None:
        row = self.db.fetch_one("SELECT * FROM workflow WHERE id=?", [workflow_id])
        return Workflow(**row) if row else None

    def get_default_for_type(self, project_id: int, task_type: str) -> Workflow | None:
        row = self.db.fetch_one(
            "SELECT * FROM workflow WHERE project_id=? AND task_type=? LIMIT 1",
            [project_id, task_type],
        )
        return Workflow(**row) if row else None

    def delete(self, workflow_id: int) -> None:
        self.db.execute("DELETE FROM workflow_node WHERE workflow_id=?", [workflow_id])
        self.db.execute("DELETE FROM workflow WHERE id=?", [workflow_id])


class WorkflowNodeRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, node: WorkflowNode) -> int:
        import json
        self.db.execute(
            """INSERT INTO workflow_node
               (workflow_id, agent_id, depends_on, review_gate, skill, skill_args, context_json, position)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                node.workflow_id, node.agent_id,
                json.dumps(node.depends_on), int(node.review_gate),
                node.skill, node.skill_args, json.dumps(node.context_json), node.position,
            ],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def list_by_workflow(self, workflow_id: int) -> list[WorkflowNode]:
        import json
        rows = self.db.fetch_all(
            "SELECT * FROM workflow_node WHERE workflow_id=? ORDER BY position",
            [workflow_id],
        )
        result = []
        for r in rows:
            r = dict(r)
            r["depends_on"] = json.loads(r["depends_on"])
            r["review_gate"] = bool(r["review_gate"])
            r["context_json"] = json.loads(r["context_json"])
            result.append(WorkflowNode(**r))
        return result
```

- [ ] **Step 4: Add TaskRepo, TaskNodeRunRepo**

```python
class TaskRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, t: Task) -> int:
        self.db.execute(
            """INSERT INTO task (project_id, task_type, workflow_id, title, description, status, complexity)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [t.project_id, t.task_type, t.workflow_id, t.title, t.description, t.status, t.complexity],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def get(self, task_id: int) -> Task | None:
        row = self.db.fetch_one("SELECT * FROM task WHERE id=?", [task_id])
        return Task(**row) if row else None

    def list_by_project(self, project_id: int, status: str | None = None) -> list[Task]:
        if status:
            rows = self.db.fetch_all(
                "SELECT * FROM task WHERE project_id=? AND status=? ORDER BY id DESC",
                [project_id, status],
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM task WHERE project_id=? ORDER BY id DESC",
                [project_id],
            )
        return [Task(**r) for r in rows]

    def list_pending(self) -> list[Task]:
        rows = self.db.fetch_all("SELECT * FROM task WHERE status='pending' ORDER BY id")
        return [Task(**r) for r in rows]

    def update_status(self, task_id: int, status: str) -> None:
        self.db.execute("UPDATE task SET status=? WHERE id=?", [status, task_id])

    def update(self, t: Task) -> None:
        self.db.execute(
            """UPDATE task SET title=?, description=?, task_type=?, workflow_id=?, status=?,
               complexity=? WHERE id=?""",
            [t.title, t.description, t.task_type, t.workflow_id, t.status, t.complexity, t.id],
        )


class TaskNodeRunRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, run: TaskNodeRun) -> int:
        import json
        self.db.execute(
            """INSERT INTO task_node_run (task_id, node_id, agent_id, status, result_json)
               VALUES (?, ?, ?, ?, ?)""",
            [run.task_id, run.node_id, run.agent_id, run.status, json.dumps(run.result_json)],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def update(self, run: TaskNodeRun) -> None:
        import json
        self.db.execute(
            """UPDATE task_node_run SET status=?, result_json=?, started_at=?,
               finished_at=? WHERE id=?""",
            [run.status, json.dumps(run.result_json), run.started_at, run.finished_at, run.id],
        )

    def list_by_task(self, task_id: int) -> list[TaskNodeRun]:
        import json
        rows = self.db.fetch_all(
            "SELECT * FROM task_node_run WHERE task_id=? ORDER BY id",
            [task_id],
        )
        result = []
        for r in rows:
            r = dict(r)
            r["result_json"] = json.loads(r["result_json"])
            result.append(TaskNodeRun(**r))
        return result
```

- [ ] **Step 5: Add KnownIssueRepo and ConstraintRuleRepo**

```python
class KnownIssueRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, issue: KnownIssue) -> int:
        self.db.execute(
            """INSERT INTO known_issue (project_id, error_pattern, root_cause, rule_update, level)
               VALUES (?, ?, ?, ?, ?)""",
            [issue.project_id, issue.error_pattern, issue.root_cause, issue.rule_update, issue.level],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[KnownIssue]:
        return [KnownIssue(**r) for r in self.db.fetch_all(
            "SELECT * FROM known_issue WHERE project_id=? ORDER BY id DESC", [project_id]
        )]

    def list_global(self) -> list[KnownIssue]:
        return [KnownIssue(**r) for r in self.db.fetch_all(
            "SELECT * FROM known_issue WHERE level='global' ORDER BY id DESC"
        )]


class ConstraintRuleRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def create(self, rule: ConstraintRule) -> int:
        self.db.execute(
            "INSERT INTO constraint_rule (project_id, rule_type, content, level) VALUES (?, ?, ?, ?)",
            [rule.project_id, rule.rule_type, rule.content, rule.level],
        )
        row = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return row["id"]

    def list_by_project(self, project_id: int) -> list[ConstraintRule]:
        return [ConstraintRule(**r) for r in self.db.fetch_all(
            "SELECT * FROM constraint_rule WHERE project_id=? OR level='global' ORDER BY id",
            [project_id],
        )]


class SkillMappingRepo:
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    def get_for_role(self, agent_role: str, project_id: int | None = None) -> list[SkillMapping]:
        base = self.db.fetch_all(
            "SELECT * FROM skill_mapping WHERE agent_role=? AND project_id IS NULL",
            [agent_role],
        )
        if project_id:
            overrides = self.db.fetch_all(
                "SELECT * FROM skill_mapping WHERE agent_role=? AND project_id=?",
                [agent_role, project_id],
            )
            return [SkillMapping(**r) for r in (overrides or base)]
        return [SkillMapping(**r) for r in base]
```

- [ ] **Step 6: Create tests/test_db/test_repositories.py**

```python
from src.db.repositories import ProjectRepo, RepositoryRepo, AgentRepo, WorkflowRepo, WorkflowNodeRepo, TaskRepo, TaskNodeRunRepo, KnownIssueRepo
from src.models import Project, Repository, Workflow, WorkflowNode, Task, TaskNodeRun, KnownIssue

def test_project_crud(tmp_db):
    repo = ProjectRepo(tmp_db)
    pid = repo.create(Project(name="test-proj", description="desc"))
    assert pid > 0

    p = repo.get(pid)
    assert p.name == "test-proj"

    p.description = "updated"
    repo.update(p)
    assert repo.get(pid).description == "updated"

    all_projects = repo.list_all()
    assert len(all_projects) == 1

def test_task_create_and_update(tmp_db):
    repo = TaskRepo(tmp_db)
    tid = repo.create(Task(project_id=1, title="implement login", task_type="development"))
    t = repo.get(tid)
    assert t.status == "pending"

    repo.update_status(tid, "running")
    assert repo.get(tid).status == "running"

def test_known_issue_create(tmp_db):
    repo = KnownIssueRepo(tmp_db)
    repo.create(KnownIssue(error_pattern="context overflow", root_cause="too much input", project_id=1))
    issues = repo.list_by_project(1)
    assert len(issues) == 1
    assert issues[0].error_pattern == "context overflow"
```

- [ ] **Step 7: Run tests and commit**

```bash
pytest tests/test_db/test_repositories.py -v
```
Expected: 3 PASS.

```bash
git add src/db/repositories.py tests/test_db/test_repositories.py
git commit -m "feat: repository classes for all core entities"
```

---

### Task 6: Workspace manager

**Files:**
- Create: `src/engine/__init__.py`
- Create: `src/engine/workspace.py`
- Test: `tests/test_engine/test_workspace.py`

- [ ] **Step 1: Create src/engine/workspace.py**

```python
import subprocess
from pathlib import Path
from src.config import WORKSPACE_ROOT

class WorkspaceManager:
    def __init__(self, root: Path | None = None):
        self.root = root or WORKSPACE_ROOT

    def repo_bare_path(self, project_name: str, repo_name: str) -> Path:
        return self.root / project_name / "repos" / f"{repo_name}.git"

    def worktree_path(self, project_name: str, task_id: int, repo_name: str) -> Path:
        return self.root / project_name / "worktrees" / f"task-{task_id}" / repo_name

    def ensure_bare_clone(self, project_name: str, repo_name: str, git_url: str) -> Path:
        bare_path = self.repo_bare_path(project_name, repo_name)
        if not bare_path.exists():
            bare_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--bare", git_url, str(bare_path)],
                check=True, capture_output=True,
            )
        else:
            subprocess.run(
                ["git", "-C", str(bare_path), "fetch", "--all"],
                check=True, capture_output=True,
            )
        return bare_path

    def create_worktree(self, project_name: str, task_id: int,
                        repo_name: str, base_branch: str = "master") -> Path:
        bare_path = self.ensure_bare_clone(project_name, repo_name, "")
        wt_path = self.worktree_path(project_name, task_id, repo_name)
        if not wt_path.exists():
            branch = f"harness/task-{task_id}"
            wt_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "-C", str(bare_path), "worktree", "add", str(wt_path), "-b", branch,
                 f"origin/{base_branch}"],
                check=True, capture_output=True,
            )
        return wt_path

    def remove_worktree(self, project_name: str, task_id: int, repo_name: str) -> None:
        bare_path = self.repo_bare_path(project_name, repo_name)
        wt_path = self.worktree_path(project_name, task_id, repo_name)
        if wt_path.exists():
            subprocess.run(
                ["git", "-C", str(bare_path), "worktree", "remove", str(wt_path), "--force"],
                check=True, capture_output=True,
            )
```

- [ ] **Step 2: Create tests/test_engine/test_workspace.py**

```python
import subprocess
from pathlib import Path
from src.engine.workspace import WorkspaceManager

def _setup_remote(tmp_path: Path) -> str:
    remote = tmp_path / "remote"
    remote.mkdir()
    subprocess.run(["git", "-C", str(remote), "init", "-b", "master"], check=True)
    subprocess.run(["git", "-C", str(remote), "config", "user.email", "test@test"], check=True)
    subprocess.run(["git", "-C", str(remote), "config", "user.name", "test"], check=True)
    (remote / "readme.md").write_text("# test")
    subprocess.run(["git", "-C", str(remote), "add", "."], check=True)
    subprocess.run(["git", "-C", str(remote), "commit", "-m", "init"], check=True)
    return str(remote)

def test_bare_clone_and_worktree(tmp_path: Path):
    remote = _setup_remote(tmp_path)
    wm = WorkspaceManager(root=tmp_path / "workspace")

    bare = wm.ensure_bare_clone("proj1", "repo1", remote)
    assert bare.exists()
    assert (bare / "HEAD").exists()

    wt = wm.create_worktree("proj1", task_id=42, repo_name="repo1", base_branch="master")
    assert wt.exists()
    assert (wt / "readme.md").exists()

    wm.remove_worktree("proj1", 42, "repo1")
    assert not wt.exists()
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_engine/test_workspace.py -v
```
Expected: 1 PASS.

```bash
git add src/engine/__init__.py src/engine/workspace.py tests/test_engine/test_workspace.py
git commit -m "feat: workspace manager with git bare clone and worktree support"
```

---

### Task 7: DAG parser and scheduler

**Files:**
- Create: `src/engine/dag.py`
- Test: `tests/test_engine/test_dag.py`

- [ ] **Step 1: Create src/engine/dag.py**

```python
from src.models import WorkflowNode

def parse_dag(nodes: list[WorkflowNode]) -> dict:
    """Parse a list of workflow nodes into a DAG structure.
    Returns: {node_id: {"node": WorkflowNode, "deps": [dep_node_ids], "dependents": [dep_node_ids]}}
    """
    dag = {}
    for n in nodes:
        dag[n.id] = {"node": n, "deps": list(n.depends_on), "dependents": []}
    for n in nodes:
        for dep_id in n.depends_on:
            if dep_id in dag:
                dag[dep_id]["dependents"].append(n.id)
    return dag

def get_ready_nodes(dag: dict, completed_node_ids: set[int]) -> list[WorkflowNode]:
    """Get nodes whose dependencies are all satisfied."""
    ready = []
    for nid, info in dag.items():
        if nid in completed_node_ids:
            continue
        if all(dep in completed_node_ids for dep in info["deps"]):
            ready.append(info["node"])
    return ready

def group_parallel(nodes: list[WorkflowNode]) -> list[list[WorkflowNode]]:
    """Group independent nodes into parallel batches.
    Nodes with no dependencies between them run in the same batch."""
    if not nodes:
        return []
    node_ids = {n.id for n in nodes}
    batches = []
    remaining = set(nodes)
    while remaining:
        batch = []
        for n in list(remaining):
            if not any(dep in node_ids for dep in n.depends_on if dep in {m.id for m in remaining}):
                batch.append(n)
        for n in batch:
            remaining.remove(n)
        if batch:
            batches.append(batch)
        else:
            batches.append(list(remaining))
            break
    return batches

def topological_sort(dag: dict) -> list[int]:
    """Topological sort of DAG node IDs."""
    in_degree = {nid: len(info["deps"]) for nid, info in dag.items()}
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    result = []
    while queue:
        nid = queue.pop(0)
        result.append(nid)
        for dep_id in dag[nid]["dependents"]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                queue.append(dep_id)
    if len(result) != len(dag):
        raise ValueError("DAG contains a cycle")
    return result
```

- [ ] **Step 2: Create tests/test_engine/test_dag.py**

```python
from src.engine.dag import parse_dag, get_ready_nodes, group_parallel, topological_sort
from src.models import WorkflowNode

def _node(id, deps=None):
    return WorkflowNode(workflow_id=1, agent_id=1, depends_on=deps or [], id=id, position=0)

def test_parse_dag():
    nodes = [_node(1), _node(2, [1]), _node(3, [1])]
    dag = parse_dag(nodes)
    assert dag[1]["dependents"] == [2, 3]
    assert dag[2]["deps"] == [1]

def test_ready_nodes_sequential():
    nodes = [_node(1), _node(2, [1]), _node(3, [2])]
    dag = parse_dag(nodes)
    ready = get_ready_nodes(dag, set())
    assert len(ready) == 1
    assert ready[0].id == 1

    ready = get_ready_nodes(dag, {1})
    assert ready[0].id == 2

def test_group_parallel():
    nodes = [_node(1), _node(2, [1]), _node(3, [1])]
    batches = group_parallel(nodes)
    assert len(batches) == 2
    assert {n.id for n in batches[0]} == {2, 3}

def test_topological_sort():
    nodes = [_node(1), _node(2, [1]), _node(3, [1]), _node(4, [2, 3])]
    dag = parse_dag(nodes)
    order = topological_sort(dag)
    assert order.index(1) < order.index(2)
    assert order.index(1) < order.index(3)
    assert order.index(2) < order.index(4)
    assert order.index(3) < order.index(4)

def test_topological_sort_detects_cycle():
    nodes = [_node(1, [2]), _node(2, [1])]
    dag = parse_dag(nodes)
    try:
        topological_sort(dag)
        assert False, "should have raised"
    except ValueError as e:
        assert "cycle" in str(e)
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_engine/test_dag.py -v
```
Expected: 5 PASS.

```bash
git add src/engine/dag.py tests/test_engine/test_dag.py
git commit -m "feat: DAG parser with topological sort and parallel batching"
```

---

### Task 8: Context assembler

**Files:**
- Create: `src/engine/context.py`
- Test: `tests/test_engine/test_context.py`

- [ ] **Step 1: Create src/engine/context.py**

```python
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
        parts = []

        # Upstream node results
        prev_runs = self.node_run_repo.list_by_task(task.id)
        if prev_runs:
            parts.append("## Previous Stage Results")
            for run in prev_runs:
                parts.append(f"- Node {run.node_id}: status={run.status}")
                if run.result_json:
                    for k, v in run.result_json.items():
                        parts.append(f"  - {k}: {v}")

        # Relevant known issues
        issues = self.known_issue_repo.list_by_project(task.project_id)
        global_issues = self.known_issue_repo.list_global()
        all_issues = issues + global_issues
        if all_issues:
            parts.append("\n## Known Issues to Avoid")
            for issue in all_issues:
                parts.append(f"- {issue.error_pattern}: {issue.root_cause}")

        # Skills for this stage
        if node.skill:
            parts.append(f"\n## Active Skill\nUse skill: `{node.skill}`")

        return "\n".join(parts)

    def build_context(self, task: Task, node: WorkflowNode, project_name: str) -> str:
        t1 = self.build_tier1(task, project_name)
        t2 = self.build_tier2(task, node)
        return f"{t1}\n\n---\n\n{t2}"
```

- [ ] **Step 2: Create tests/test_engine/test_context.py**

```python
from src.engine.context import ContextAssembler
from src.db.repositories import (
    ProjectRepo, TaskRepo, TaskNodeRunRepo, WorkflowNodeRepo,
    KnownIssueRepo, ConstraintRuleRepo, SkillMappingRepo,
)
from src.models import Project, Task, WorkflowNode, KnownIssue, ConstraintRule

def test_build_tier1(tmp_db):
    proj_repo = ProjectRepo(tmp_db)
    pid = proj_repo.create(Project(name="test-project", description="test desc", boundary="src/"))

    cr_repo = ConstraintRuleRepo(tmp_db)
    cr_repo.create(ConstraintRule(rule_type="style", content="use snake_case", project_id=pid))

    asm = ContextAssembler(tmp_db, proj_repo, None, None, None, None, cr_repo, None)
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

    asm = ContextAssembler(tmp_db, proj_repo, None, None, None, ki_repo, None, None)
    task = Task(project_id=pid, id=1)
    node = WorkflowNode(workflow_id=1, agent_id=1, skill="superpowers:brainstorming", id=1)

    ctx = asm.build_tier2(task, node)
    assert "circular import" in ctx
    assert "superpowers:brainstorming" in ctx
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_engine/test_context.py -v
```
Expected: 2 PASS.

```bash
git add src/engine/context.py tests/test_engine/test_context.py
git commit -m "feat: context assembler with 3-tier context model"
```

---

### Task 9: Claude Code runner

**Files:**
- Create: `src/engine/runner.py`
- Test: `tests/test_engine/test_runner.py`

- [ ] **Step 1: Create src/engine/runner.py**

```python
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
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
        context_file = worktree_path / ".harness-context.md"
        context_file.write_text(context)

        prompt = self._build_prompt(node)
        cmd = self._build_command(prompt, worktree_path, node.skill)

        try:
            result = subprocess.run(
                cmd, cwd=str(worktree_path), capture_output=True, text=True, timeout=1800,
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
        context_parts = []
        if "focus_path" in node.context_json:
            context_parts.append(f"Focus on: {node.context_json['focus_path']}")
        if "rules" in node.context_json:
            context_parts.append(f"Additional rules: {', '.join(node.context_json['rules'])}")
        prefix = "\n".join(context_parts)
        if prefix:
            prefix += "\n\n---\n\n"
        return prefix + "Read the .harness-context.md file for full context and complete your assigned task."

    def _build_command(self, prompt: str, cwd: Path, skill: str) -> list[str]:
        cmd = ["claude-code", "--cwd", str(cwd)]
        if skill:
            cmd.extend(["--skill", skill])
        cmd.extend(["--prompt", prompt])
        return cmd
```

- [ ] **Step 2: Create tests/test_engine/test_runner.py**

```python
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

    task = Task(project_id=1, id=10)
    node = WorkflowNode(workflow_id=1, agent_id=2, id=3)
    wt = tmp_path / "worktree"
    wt.mkdir()

    run = runner.run(task, node, wt, "proj")
    assert run.status == "failed"
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_engine/test_runner.py -v
```
Expected: 2 PASS.

```bash
git add src/engine/runner.py tests/test_engine/test_runner.py
git commit -m "feat: Claude Code runner with skill injection and context file"
```

---

### Task 10: Orchestrator

**Files:**
- Create: `src/engine/orchestrator.py`
- Test: `tests/test_engine/test_orchestrator.py`

- [ ] **Step 1: Create src/engine/orchestrator.py**

```python
import json
from datetime import datetime
from src.db.adapter import DatabaseAdapter
from src.db.repositories import (
    ProjectRepo, TaskRepo, TaskNodeRunRepo, WorkflowRepo, WorkflowNodeRepo,
    AgentRepo, KnownIssueRepo, ConstraintRuleRepo, SkillMappingRepo,
    RepositoryRepo,
)
from src.engine.workspace import WorkspaceManager
from src.engine.dag import parse_dag, get_ready_nodes, group_parallel
from src.engine.context import ContextAssembler
from src.engine.runner import ClaudeCodeRunner
from src.models import Task, TaskNodeRun

class Orchestrator:
    def __init__(self, db: DatabaseAdapter):
        self.db = db
        self.project_repo = ProjectRepo(db)
        self.task_repo = TaskRepo(db)
        self.node_run_repo = TaskNodeRunRepo(db)
        self.workflow_repo = WorkflowRepo(db)
        self.workflow_node_repo = WorkflowNodeRepo(db)
        self.agent_repo = AgentRepo(db)
        self.known_issue_repo = KnownIssueRepo(db)
        self.constraint_rule_repo = ConstraintRuleRepo(db)
        self.skill_repo = SkillMappingRepo(db)
        self.repo_repo = RepositoryRepo(db)
        self.workspace = WorkspaceManager()
        self.context_assembler = ContextAssembler(
            db, self.project_repo, self.task_repo, self.node_run_repo,
            self.workflow_node_repo, self.known_issue_repo,
            self.constraint_rule_repo, self.skill_repo,
        )
        self.runner = ClaudeCodeRunner(self.context_assembler)
        self._callbacks = []

    def on_node_complete(self, callback):
        """Register callback(node_run) for review gate notifications."""
        self._callbacks.append(callback)

    def run_task(self, task_id: int, trigger_source: str = "web") -> None:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        self.task_repo.update_status(task_id, "running")
        project = self.project_repo.get(task.project_id)

        workflow_id = task.workflow_id
        if not workflow_id:
            wf = self.workflow_repo.get_default_for_type(task.project_id, task.task_type)
            if not wf:
                raise ValueError(f"No workflow for task type {task.task_type} in project {task.project_id}")
            workflow_id = wf.id
            task.workflow_id = workflow_id
            self.task_repo.update(task)

        nodes = self.workflow_node_repo.list_by_workflow(workflow_id)
        dag = parse_dag(nodes)
        completed = set()

        try:
            while True:
                ready = get_ready_nodes(dag, completed)
                if not ready:
                    break

                for node in ready:
                    # Prepare workspace
                    repos = self.repo_repo.list_by_project(task.project_id)
                    for repo in repos:
                        self.workspace.ensure_bare_clone(project.name, repo.name, repo.git_url)
                        self.workspace.create_worktree(project.name, task_id, repo.name, repo.default_branch)

                    wt_path = self.workspace.worktree_path(project.name, task_id, repos[0].name) if repos else None

                    # Run
                    run = TaskNodeRun(task_id=task.id, node_id=node.id, agent_id=node.agent_id)
                    run_id = self.node_run_repo.create(run)
                    run.id = run_id

                    run = self.runner.run(task, node, wt_path, project.name)
                    self.node_run_repo.update(run)

                    # Review gate check
                    if node.review_gate:
                        run.status = "waiting_review"
                        self.node_run_repo.update(run)
                        for cb in self._callbacks:
                            cb(run)

                    if run.status == "failed":
                        raise RuntimeError(f"Node {node.id} failed")

                    completed.add(node.id)

            self.task_repo.update_status(task_id, "completed" if trigger_source == "web" else "plan_ready")
        except Exception:
            self.task_repo.update_status(task_id, "failed")
            raise
```

- [ ] **Step 2: Create tests/test_engine/test_orchestrator.py**

```python
from unittest.mock import patch, MagicMock
from src.engine.orchestrator import Orchestrator
from src.db.repositories import ProjectRepo, TaskRepo, WorkflowRepo, WorkflowNodeRepo, RepositoryRepo
from src.models import Project, Task, Workflow, WorkflowNode, Repository

def setup_test_data(db):
    proj_repo = ProjectRepo(db)
    pid = proj_repo.create(Project(name="test-proj", description="", boundary=""))

    repo_repo = RepositoryRepo(db)
    repo_repo.create(Repository(project_id=pid, name="main", git_url="/tmp/fake"))

    wf_repo = WorkflowRepo(db)
    wid = wf_repo.create(Workflow(project_id=pid, name="simple", task_type="development"))

    node_repo = WorkflowNodeRepo(db)
    node_repo.create(WorkflowNode(workflow_id=wid, agent_id=1, id=1, position=0))
    node_repo.create(WorkflowNode(workflow_id=wid, agent_id=2, id=2, depends_on=[1],
                                   review_gate=True, position=1))

    task_repo = TaskRepo(db)
    tid = task_repo.create(Task(project_id=pid, task_type="development", workflow_id=wid,
                                title="test task"))

    return pid, wid, tid

@patch("src.engine.orchestrator.WorkspaceManager")
@patch("src.engine.orchestrator.ClaudeCodeRunner")
def test_orchestrator_runs_dag(mock_runner_class, mock_ws_class, tmp_db):
    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(status="done", id=1, node_id=1, agent_id=1,
                                              result_json={})
    mock_runner_class.return_value = mock_runner

    mock_ws = MagicMock()
    mock_ws.worktree_path.return_value = MagicMock()
    mock_ws_class.return_value = mock_ws

    pid, wid, tid = setup_test_data(tmp_db)
    orch = Orchestrator(tmp_db)
    orch.run_task(tid, trigger_source="web")

    task = orch.task_repo.get(tid)
    assert task.status == "completed"
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_engine/test_orchestrator.py -v
```
Expected: 1 PASS.

```bash
git add src/engine/orchestrator.py tests/test_engine/test_orchestrator.py
git commit -m "feat: orchestrator wiring DAG, workspace, context, and runner together"
```

---

### Task 11: FastAPI app setup + project routes

**Files:**
- Create: `src/web/__init__.py`
- Create: `src/web/app.py`
- Create: `src/web/deps.py`
- Create: `src/web/routes/__init__.py`
- Create: `src/web/routes/projects.py`
- Test: `tests/test_web/__init__.py`
- Test: `tests/test_web/test_projects.py`

- [ ] **Step 1: Create src/web/deps.py**

```python
from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data
from src.engine.orchestrator import Orchestrator
from src.config import DB_PATH

_db = SQLiteAdapter(str(DB_PATH))
create_schema(_db)
seed_data(_db)

def get_db():
    return _db

def get_orchestrator():
    return Orchestrator(_db)
```

- [ ] **Step 2: Create src/web/app.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.web.routes import projects, workflows, agents, tasks, issues
from src.web.ws import ws_router

def create_app() -> FastAPI:
    app = FastAPI(title="xx-harness", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(issues.router, prefix="/api/issues", tags=["issues"])
    app.include_router(ws_router)
    return app

app = create_app()
```

- [ ] **Step 3: Create src/web/routes/projects.py**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import ProjectRepo, RepositoryRepo
from src.models import Project, Repository
from src.web.deps import get_db

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    boundary: str = ""

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    boundary: str | None = None

class RepoCreate(BaseModel):
    name: str
    git_url: str
    default_branch: str = "master"

@router.get("/")
def list_projects(db: DatabaseAdapter = Depends(get_db)):
    return ProjectRepo(db).list_all()

@router.post("/")
def create_project(body: ProjectCreate, db: DatabaseAdapter = Depends(get_db)):
    pid = ProjectRepo(db).create(Project(name=body.name, description=body.description, boundary=body.boundary))
    return {"id": pid}

@router.get("/{project_id}")
def get_project(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    p = ProjectRepo(db).get(project_id)
    if not p:
        return {"error": "not found"}, 404
    return p

@router.put("/{project_id}")
def update_project(project_id: int, body: ProjectUpdate, db: DatabaseAdapter = Depends(get_db)):
    repo = ProjectRepo(db)
    p = repo.get(project_id)
    if not p:
        return {"error": "not found"}, 404
    if body.name is not None:
        p.name = body.name
    if body.description is not None:
        p.description = body.description
    if body.boundary is not None:
        p.boundary = body.boundary
    repo.update(p)
    return p

@router.delete("/{project_id}")
def delete_project(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    ProjectRepo(db).delete(project_id)
    return {"ok": True}

@router.get("/{project_id}/repos")
def list_repos(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    return RepositoryRepo(db).list_by_project(project_id)

@router.post("/{project_id}/repos")
def add_repo(project_id: int, body: RepoCreate, db: DatabaseAdapter = Depends(get_db)):
    rid = RepositoryRepo(db).create(Repository(
        project_id=project_id, name=body.name,
        git_url=body.git_url, default_branch=body.default_branch,
    ))
    return {"id": rid}

@router.delete("/{project_id}/repos/{repo_id}")
def remove_repo(project_id: int, repo_id: int, db: DatabaseAdapter = Depends(get_db)):
    RepositoryRepo(db).delete(repo_id)
    return {"ok": True}
```

- [ ] **Step 4: Create tests/test_web/test_projects.py**

```python
from fastapi.testclient import TestClient
from src.web.app import app
from src.web.deps import get_db, _db

_client = TestClient(app)

def test_create_and_list_projects():
    resp = _client.post("/api/projects/", json={"name": "web-test-proj", "description": "test"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = _client.get("/api/projects/")
    projects = resp.json()
    assert any(p["id"] == pid for p in projects)
```

- [ ] **Step 5: Run tests and commit**

```bash
pytest tests/test_web/test_projects.py -v -s
```
Expected: PASS.

```bash
git add src/web/ src/web/routes/ tests/test_web/
git commit -m "feat: FastAPI app with project CRUD routes"
```

---

### Task 12: Workflow and agent routes

**Files:**
- Create: `src/web/routes/workflows.py`
- Create: `src/web/routes/agents.py`
- Test: `tests/test_web/test_workflows.py`

- [ ] **Step 1: Create src/web/routes/workflows.py**

```python
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import WorkflowRepo, WorkflowNodeRepo, AgentRepo
from src.models import Workflow, WorkflowNode
from src.web.deps import get_db

router = APIRouter()

class NodeDef(BaseModel):
    agent_name: str
    depends_on: list[int] = []
    review_gate: bool = False
    skill: str = ""
    skill_args: str = ""
    context_json: dict = {}

class WorkflowCreate(BaseModel):
    name: str
    task_type: str = "custom"
    project_id: int
    nodes: list[NodeDef] = []

@router.get("/project/{project_id}")
def list_workflows(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    workflows = WorkflowRepo(db).list_by_project(project_id)
    result = []
    node_repo = WorkflowNodeRepo(db)
    for wf in workflows:
        nodes = node_repo.list_by_workflow(wf.id)
        result.append({"workflow": wf, "nodes": nodes})
    return result

@router.post("/")
def create_workflow(body: WorkflowCreate, db: DatabaseAdapter = Depends(get_db)):
    wf_repo = WorkflowRepo(db)
    wf_id = wf_repo.create(Workflow(
        project_id=body.project_id, name=body.name, task_type=body.task_type,
    ))

    node_repo = WorkflowNodeRepo(db)
    agent_repo = AgentRepo(db)
    for i, nd in enumerate(body.nodes):
        agent = agent_repo.get_by_name(nd.agent_name)
        if not agent:
            return {"error": f"agent {nd.agent_name} not found"}, 400
        node_repo.create(WorkflowNode(
            workflow_id=wf_id, agent_id=agent.id,
            depends_on=nd.depends_on, review_gate=nd.review_gate,
            skill=nd.skill, skill_args=nd.skill_args,
            context_json=nd.context_json, position=i,
        ))

    return {"id": wf_id}

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: DatabaseAdapter = Depends(get_db)):
    WorkflowRepo(db).delete(workflow_id)
    return {"ok": True}
```

- [ ] **Step 2: Create src/web/routes/agents.py**

```python
from fastapi import APIRouter, Depends
from src.db.adapter import DatabaseAdapter
from src.db.repositories import AgentRepo
from src.web.deps import get_db

router = APIRouter()

@router.get("/")
def list_agents(db: DatabaseAdapter = Depends(get_db)):
    return AgentRepo(db).list_all()
```

- [ ] **Step 3: Create tests/test_web/test_workflows.py**

```python
from fastapi.testclient import TestClient
from src.web.app import app

_client = TestClient(app)

def test_create_and_list_workflow():
    # Create project first
    resp = _client.post("/api/projects/", json={"name": "wf-test-proj"})
    pid = resp.json()["id"]

    resp = _client.post("/api/workflows/", json={
        "name": "standard",
        "task_type": "development",
        "project_id": pid,
        "nodes": [
            {"agent_name": "researcher"},
            {"agent_name": "planner", "depends_on": [1], "review_gate": True},
        ]
    })
    assert resp.status_code == 200

    resp = _client.get(f"/api/workflows/project/{pid}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert len(resp.json()[0]["nodes"]) == 2
```

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/test_web/test_workflows.py -v -s
```
Expected: PASS.

```bash
git add src/web/routes/workflows.py src/web/routes/agents.py tests/test_web/test_workflows.py
git commit -m "feat: workflow and agent API routes"
```

---

### Task 13: Task routes + WebSocket trace

**Files:**
- Create: `src/web/routes/tasks.py`
- Create: `src/web/ws.py`
- Test: `tests/test_web/test_tasks.py`

- [ ] **Step 1: Create src/web/routes/tasks.py**

```python
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import TaskRepo, TaskNodeRunRepo, WorkflowRepo
from src.models import Task
from src.web.deps import get_db, get_orchestrator
from src.engine.orchestrator import Orchestrator

router = APIRouter()

class TaskCreate(BaseModel):
    project_id: int
    title: str
    task_type: str = "development"
    description: str = ""
    complexity: str = "medium"
    workflow_id: int | None = None

@router.get("/project/{project_id}")
def list_tasks(project_id: int, status: str | None = None, db: DatabaseAdapter = Depends(get_db)):
    return TaskRepo(db).list_by_project(project_id, status)

@router.post("/")
def create_task(body: TaskCreate, db: DatabaseAdapter = Depends(get_db)):
    tid = TaskRepo(db).create(Task(
        project_id=body.project_id, task_type=body.task_type,
        workflow_id=body.workflow_id, title=body.title,
        description=body.description, complexity=body.complexity,
    ))
    return {"id": tid}

@router.post("/{task_id}/start")
def start_task(task_id: int, background_tasks: BackgroundTasks,
               db: DatabaseAdapter = Depends(get_db)):
    task = TaskRepo(db).get(task_id)
    if not task:
        return {"error": "not found"}, 404

    orch = get_orchestrator()
    background_tasks.add_task(orch.run_task, task_id, trigger_source="web")
    return {"ok": True, "status": "starting"}

@router.get("/{task_id}")
def get_task(task_id: int, db: DatabaseAdapter = Depends(get_db)):
    task = TaskRepo(db).get(task_id)
    if not task:
        return {"error": "not found"}, 404
    runs = TaskNodeRunRepo(db).list_by_task(task_id)
    return {"task": task, "node_runs": runs}

@router.get("/{task_id}/trace")
def get_task_trace(task_id: int, db: DatabaseAdapter = Depends(get_db)):
    runs = TaskNodeRunRepo(db).list_by_task(task_id)
    return {"task_id": task_id, "runs": [{"node_id": r.node_id, "status": r.status,
            "result": r.result_json} for r in runs]}
```

- [ ] **Step 2: Create src/web/ws.py**

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()
active_connections: dict[int, list[WebSocket]] = {}

@ws_router.websocket("/ws/tasks/{task_id}")
async def task_trace(ws: WebSocket, task_id: int):
    await ws.accept()
    active_connections.setdefault(task_id, []).append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        active_connections[task_id].remove(ws)
```

- [ ] **Step 3: Create tests/test_web/test_tasks.py**

```python
from fastapi.testclient import TestClient
from src.web.app import app

_client = TestClient(app)

def test_create_and_start_task():
    resp = _client.post("/api/projects/", json={"name": "task-test-proj"})
    pid = resp.json()["id"]

    resp = _client.post("/api/workflows/", json={
        "name": "simple", "task_type": "development", "project_id": pid,
        "nodes": [{"agent_name": "researcher"}],
    })
    assert resp.status_code == 200

    resp = _client.post("/api/tasks/", json={
        "project_id": pid, "title": "implement login", "task_type": "development",
    })
    assert resp.status_code == 200
    tid = resp.json()["id"]

    resp = _client.get(f"/api/tasks/{tid}")
    assert resp.status_code == 200
    assert resp.json()["task"]["title"] == "implement login"
```

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/test_web/test_tasks.py -v -s
```
Expected: PASS.

```bash
git add src/web/routes/tasks.py src/web/ws.py tests/test_web/test_tasks.py
git commit -m "feat: task routes with background start and WebSocket trace"
```

---

### Task 14: KnownIssue routes (learning loop)

**Files:**
- Create: `src/web/routes/issues.py`
- Test: `tests/test_web/test_issues.py`

- [ ] **Step 1: Create src/web/routes/issues.py**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import KnownIssueRepo, ConstraintRuleRepo
from src.models import KnownIssue, ConstraintRule
from src.web.deps import get_db

router = APIRouter()

class IssueCreate(BaseModel):
    project_id: int | None = None
    error_pattern: str
    root_cause: str = ""
    rule_update: str = ""
    level: str = "project"

class RuleCreate(BaseModel):
    project_id: int | None = None
    rule_type: str
    content: str
    level: str = "project"

@router.get("/project/{project_id}")
def list_issues(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    return KnownIssueRepo(db).list_by_project(project_id)

@router.post("/")
def create_issue(body: IssueCreate, db: DatabaseAdapter = Depends(get_db)):
    rid = KnownIssueRepo(db).create(KnownIssue(
        project_id=body.project_id, error_pattern=body.error_pattern,
        root_cause=body.root_cause, rule_update=body.rule_update,
        level=body.level,
    ))
    return {"id": rid}

@router.post("/{issue_id}/promote")
def promote_to_global(issue_id: int, db: DatabaseAdapter = Depends(get_db)):
    """Promote a project-level issue to global."""
    issues = KnownIssueRepo(db).list_by_project(0)
    issue = next((i for i in KnownIssueRepo(db).list_global() if i.id == issue_id), None)
    if not issue:
        all_issues = KnownIssueRepo(db).list_by_project(0)
        issue = next((i for i in all_issues if i.id == issue_id), None)
    if not issue:
        return {"error": "not found"}, 404
    issue.level = "global"
    # Re-insert as global
    KnownIssueRepo(db).create(issue)
    return {"ok": True}

@router.get("/rules/project/{project_id}")
def list_rules(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    return ConstraintRuleRepo(db).list_by_project(project_id)

@router.post("/rules")
def create_rule(body: RuleCreate, db: DatabaseAdapter = Depends(get_db)):
    rid = ConstraintRuleRepo(db).create(ConstraintRule(
        project_id=body.project_id, rule_type=body.rule_type,
        content=body.content, level=body.level,
    ))
    return {"id": rid}
```

- [ ] **Step 2: Create tests/test_web/test_issues.py**

```python
from fastapi.testclient import TestClient
from src.web.app import app

_client = TestClient(app)

def test_create_issue():
    resp = _client.post("/api/projects/", json={"name": "issue-test-proj"})
    pid = resp.json()["id"]

    resp = _client.post("/api/issues/", json={
        "project_id": pid, "error_pattern": "agent forgets dev server setup",
        "root_cause": "no init.sh in repo",
    })
    assert resp.status_code == 200

    resp = _client.get(f"/api/issues/project/{pid}")
    assert len(resp.json()) == 1
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/test_web/test_issues.py -v -s
```
Expected: PASS.

```bash
git add src/web/routes/issues.py tests/test_web/test_issues.py
git commit -m "feat: known issues and constraint rules API routes"
```

---

### Task 15: React frontend — project setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api.ts`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "xx-harness-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3",
    "react-dom": "^18.3",
    "react-router-dom": "^6.28"
  },
  "devDependencies": {
    "@types/react": "^18.3",
    "@types/react-dom": "^18.3",
    "@vitejs/plugin-react": "^4.3",
    "typescript": "^5.6",
    "vite": "^6.0"
  }
}
```

- [ ] **Step 2: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8720", "/ws": { target: "ws://localhost:8720", ws: true } } },
});
```

- [ ] **Step 4: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head><meta charset="UTF-8" /><title>xx-harness</title></head>
  <body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>
</html>
```

- [ ] **Step 5: Create frontend/src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter><App /></BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 6: Create frontend/src/api.ts**

```typescript
const BASE = "/api";

async function request(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  projects: {
    list: () => request("/projects/"),
    create: (data: { name: string; description?: string; boundary?: string }) =>
      request("/projects/", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number) => request(`/projects/${id}`),
    delete: (id: number) => request(`/projects/${id}`, { method: "DELETE" }),
    addRepo: (projectId: number, data: { name: string; git_url: string; default_branch?: string }) =>
      request(`/projects/${projectId}/repos`, { method: "POST", body: JSON.stringify(data) }),
    listRepos: (projectId: number) => request(`/projects/${projectId}/repos`),
  },
  workflows: {
    listByProject: (projectId: number) => request(`/workflows/project/${projectId}`),
    create: (data: any) => request("/workflows/", { method: "POST", body: JSON.stringify(data) }),
    delete: (id: number) => request(`/workflows/${id}`, { method: "DELETE" }),
  },
  agents: {
    list: () => request("/agents/"),
  },
  tasks: {
    listByProject: (projectId: number, status?: string) =>
      request(`/tasks/project/${projectId}${status ? `?status=${status}` : ""}`),
    create: (data: any) => request("/tasks/", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number) => request(`/tasks/${id}`),
    start: (id: number) => request(`/tasks/${id}/start`, { method: "POST" }),
    trace: (id: number) => request(`/tasks/${id}/trace`),
  },
  issues: {
    listByProject: (projectId: number) => request(`/issues/project/${projectId}`),
    create: (data: any) => request("/issues/", { method: "POST", body: JSON.stringify(data) }),
  },
};
```

- [ ] **Step 7: Create frontend/src/App.tsx**

```tsx
import { Routes, Route, Link } from "react-router-dom";
import { ProjectList } from "./pages/ProjectList";
import { ProjectDetail } from "./pages/ProjectDetail";
import { WorkflowEditor } from "./pages/WorkflowEditor";
import { TaskCreate } from "./pages/TaskCreate";
import { TaskTrace } from "./pages/TaskTrace";

export default function App() {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: 20 }}>
      <nav style={{ marginBottom: 24, display: "flex", gap: 16 }}>
        <Link to="/">项目</Link>
      </nav>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/projects/:id/workflows/new" element={<WorkflowEditor />} />
        <Route path="/projects/:id/tasks/new" element={<TaskCreate />} />
        <Route path="/tasks/:id/trace" element={<TaskTrace />} />
      </Routes>
    </div>
  );
}
```

- [ ] **Step 8: Install and build check**

```bash
cd frontend && npm install && npx tsc --noEmit
```
Expected: no type errors.

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: React frontend scaffolding with Vite, routing, and API client"
```

---

### Task 16: Frontend — ProjectList and ProjectDetail pages

**Files:**
- Create: `frontend/src/pages/ProjectList.tsx`
- Create: `frontend/src/pages/ProjectDetail.tsx`
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/components/StatusBadge.tsx`

- [ ] **Step 1: Create ProjectList.tsx**

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export function ProjectList() {
  const [projects, setProjects] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => { api.projects.list().then(setProjects); }, []);

  async function handleCreate() {
    await api.projects.create({ name, description });
    setName(""); setDescription("");
    setShowForm(false);
    api.projects.list().then(setProjects);
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>项目</h1>
        <button onClick={() => setShowForm(!showForm)}>+ 新建项目</button>
      </div>
      {showForm && (
        <div style={{ border: "1px solid #ccc", padding: 16, marginBottom: 16 }}>
          <input placeholder="项目名" value={name} onChange={e => setName(e.target.value)} />
          <input placeholder="描述" value={description} onChange={e => setDescription(e.target.value)} style={{ marginLeft: 8 }} />
          <button onClick={handleCreate} style={{ marginLeft: 8 }}>创建</button>
        </div>
      )}
      <table width="100%">
        <thead><tr><th>ID</th><th>名称</th><th>描述</th><th>操作</th></tr></thead>
        <tbody>
          {projects.map((p: any) => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td><Link to={`/projects/${p.id}`}>{p.name}</Link></td>
              <td>{p.description}</td>
              <td>
                <Link to={`/projects/${p.id}/tasks/new`}><button>新建任务</button></Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Create ProjectDetail.tsx**

```tsx
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const [project, setProject] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);

  useEffect(() => {
    api.projects.get(projectId).then(setProject);
    api.tasks.listByProject(projectId).then(setTasks);
    api.workflows.listByProject(projectId).then(setWorkflows);
    api.issues.listByProject(projectId).then(setIssues);
  }, [projectId]);

  if (!project) return <div>加载中...</div>;

  return (
    <div>
      <h1>{project.name}</h1>
      <p>{project.description}</p>

      <div style={{ display: "flex", gap: 24, marginTop: 24 }}>
        <Link to={`/projects/${projectId}/workflows/new`}><button>+ 新建工作流</button></Link>
        <Link to={`/projects/${projectId}/tasks/new`}><button>+ 新建任务</button></Link>
      </div>

      <h2 style={{ marginTop: 32 }}>任务 ({tasks.length})</h2>
      <table width="100%">
        <thead><tr><th>ID</th><th>标题</th><th>类型</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          {tasks.map((t: any) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.title}</td>
              <td>{t.task_type}</td>
              <td>{t.status}</td>
              <td><Link to={`/tasks/${t.id}/trace`}>查看</Link></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>工作流 ({workflows.length})</h2>
      {workflows.map((w: any) => (
        <div key={w.workflow.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8 }}>
          <strong>{w.workflow.name}</strong> ({w.workflow.task_type}) — {w.nodes.length} 个节点
        </div>
      ))}

      <h2>已知问题 ({issues.length})</h2>
      {issues.map((i: any) => (
        <div key={i.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8 }}>
          <strong>{i.error_pattern}</strong>: {i.root_cause}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ProjectList.tsx frontend/src/pages/ProjectDetail.tsx
git commit -m "feat: project list and detail pages"
```

---

### Task 17: Frontend — WorkflowEditor and TaskCreate pages

**Files:**
- Create: `frontend/src/pages/WorkflowEditor.tsx`
- Create: `frontend/src/pages/TaskCreate.tsx`

- [ ] **Step 1: Create WorkflowEditor.tsx**

```tsx
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [agents, setAgents] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [taskType, setTaskType] = useState("development");
  const [nodes, setNodes] = useState<{ agent_name: string; depends_on: number[]; review_gate: boolean; skill: string }[]>([{ agent_name: "researcher", depends_on: [], review_gate: false, skill: "" }]);

  useEffect(() => { api.agents.list().then(setAgents); }, []);

  function addNode() {
    setNodes([...nodes, { agent_name: "executor", depends_on: [], review_gate: false, skill: "" }]);
  }

  async function handleSave() {
    await api.workflows.create({ name, task_type: taskType, project_id: projectId, nodes });
    navigate(`/projects/${projectId}`);
  }

  const agentOptions = agents.map(a => a.name);

  return (
    <div>
      <h1>新建工作流</h1>
      <div>
        <label>名称: <input value={name} onChange={e => setName(e.target.value)} /></label>
        <label style={{ marginLeft: 16 }}>类型:
          <select value={taskType} onChange={e => setTaskType(e.target.value)}>
            <option value="development">development</option>
            <option value="exploration">exploration</option>
            <option value="testing">testing</option>
            <option value="deployment">deployment</option>
            <option value="custom">custom</option>
          </select>
        </label>
      </div>
      <h2 style={{ marginTop: 24 }}>节点 ({nodes.length})</h2>
      {nodes.map((n, i) => (
        <div key={i} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8 }}>
          <strong>节点 {i + 1}</strong>
          <div>
            Agent: <select value={n.agent_name} onChange={e => {
              const next = [...nodes]; next[i] = { ...next[i], agent_name: e.target.value }; setNodes(next);
            }}>
              {agentOptions.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            依赖节点 (逗号分隔的序号): <input value={n.depends_on.join(",")} onChange={e => {
              const next = [...nodes]; next[i] = { ...next[i], depends_on: e.target.value.split(",").map(Number).filter(n => n > 0) }; setNodes(next);
            }} />
          </div>
          <div>
            Skill: <input value={n.skill} onChange={e => {
              const next = [...nodes]; next[i] = { ...next[i], skill: e.target.value }; setNodes(next);
            }} placeholder="如 superpowers:brainstorming" />
          </div>
          <label>
            <input type="checkbox" checked={n.review_gate} onChange={e => {
              const next = [...nodes]; next[i] = { ...next[i], review_gate: e.target.checked }; setNodes(next);
            }} /> 审查门
          </label>
        </div>
      ))}
      <button onClick={addNode} style={{ marginRight: 8 }}>+ 添加节点</button>
      <button onClick={handleSave}>保存</button>
    </div>
  );
}
```

- [ ] **Step 2: Create TaskCreate.tsx**

```tsx
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";

export function TaskCreate() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [taskType, setTaskType] = useState("development");
  const [description, setDescription] = useState("");
  const [workflowId, setWorkflowId] = useState<number | null>(null);

  useEffect(() => {
    api.workflows.listByProject(projectId).then(setWorkflows);
  }, [projectId]);

  async function handleCreate() {
    const res = await api.tasks.create({
      project_id: projectId, title, task_type: taskType,
      description, workflow_id: workflowId || null,
    });
    if (confirm("任务已创建，要立即开始吗？")) {
      await api.tasks.start(res.id);
    }
    navigate(`/tasks/${res.id}/trace`);
  }

  const matchingWorkflows = workflows.filter((w: any) => w.workflow.task_type === taskType);

  return (
    <div>
      <h1>新建任务</h1>
      <div>
        <label>标题: <input value={title} onChange={e => setTitle(e.target.value)} /></label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label>类型:
          <select value={taskType} onChange={e => { setTaskType(e.target.value); setWorkflowId(null); }}>
            <option value="development">开发</option>
            <option value="exploration">探索</option>
            <option value="testing">测试</option>
          </select>
        </label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label>工作流:
          <select value={workflowId ?? ""} onChange={e => setWorkflowId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">自动</option>
            {matchingWorkflows.map((w: any) => (
              <option key={w.workflow.id} value={w.workflow.id}>{w.workflow.name}</option>
            ))}
          </select>
        </label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label>描述:<br /><textarea rows={4} value={description} onChange={e => setDescription(e.target.value)} /></label>
      </div>
      <button onClick={handleCreate} style={{ marginTop: 16 }}>创建并开始</button>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/WorkflowEditor.tsx frontend/src/pages/TaskCreate.tsx
git commit -m "feat: workflow editor and task creation pages"
```

---

### Task 18: Frontend — TaskTrace page + DAG view

**Files:**
- Create: `frontend/src/pages/TaskTrace.tsx`
- Create: `frontend/src/components/DAGView.tsx`

- [ ] **Step 1: Create TaskTrace.tsx**

```tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { DAGView } from "../components/DAGView";

export function TaskTrace() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      api.tasks.trace(Number(id)).then(setData);
    }, 2000);
    api.tasks.trace(Number(id)).then(setData);
    return () => clearInterval(interval);
  }, [id]);

  if (!data) return <div>加载中...</div>;

  return (
    <div>
      <h1>任务 #{data.task_id} 执行追踪</h1>
      <div style={{ marginTop: 16 }}>
        {data.runs.map((r: any) => (
          <div key={r.node_id} style={{
            border: "1px solid #ccc", padding: 12, marginBottom: 8,
            background: r.status === "done" ? "#e8f5e9" : r.status === "failed" ? "#ffebee" : r.status === "waiting_review" ? "#fff3e0" : "#f5f5f5",
          }}>
            <strong>节点 {r.node_id}</strong>: {r.status}
            {r.result && <pre style={{ fontSize: 12, marginTop: 4 }}>{JSON.stringify(r.result, null, 2)}</pre>}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create DAGView.tsx**

```tsx
export function DAGView({ runs }: { runs: any[] }) {
  const nodeStyle = (status: string) => ({
    padding: "8px 16px", borderRadius: 4, display: "inline-block",
    background: status === "done" ? "#4caf50" : status === "running" ? "#2196f3" :
                status === "failed" ? "#f44336" : status === "waiting_review" ? "#ff9800" : "#9e9e9e",
    color: "#fff", fontSize: 14,
  });

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
      {runs.map((r, i) => (
        <div key={r.node_id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={nodeStyle(r.status)}>
            {r.node_id}
          </div>
          {i < runs.length - 1 && <span>→</span>}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/TaskTrace.tsx frontend/src/components/DAGView.tsx
git commit -m "feat: task trace page with node status visualization"
```

---

### Task 19: Claude Code entry point (CLAUDE.md injection)

**Files:**
- Create: `src/harness_claude.py`

- [ ] **Step 1: Create src/harness_claude.py**

```python
"""Entry point for Claude Code dialogue — injects harness context.

Usage: Place in project's CLAUDE.md or invoke as a hook.
When Claude Code starts in a harness-managed project, it reads the SQLite
database and injects relevant harness context into the session.
"""
import sys
from pathlib import Path
from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data
from src.db.repositories import ProjectRepo, TaskRepo, WorkflowNodeRepo, KnownIssueRepo, ConstraintRuleRepo
from src.config import DB_PATH

def get_harness_context(project_name: str, task_id: int | None = None) -> str:
    db = SQLiteAdapter(str(DB_PATH))
    create_schema(db)

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

    # Tier 1: Constraints
    cr_repo = ConstraintRuleRepo(db)
    rules = cr_repo.list_by_project(project.id)
    if rules:
        lines.append("## Constraints")
        for r in rules:
            lines.append(f"- [{r.rule_type}] {r.content}")
        lines.append("")

    # Tier 2: Active tasks
    task_repo = TaskRepo(db)
    if task_id:
        task = task_repo.get(task_id)
        if task:
            lines.append(f"## Active Task: {task.title}")
            lines.append(f"Type: {task.task_type} | Status: {task.status}")
            lines.append(f"Description: {task.description}")
            lines.append("")

    # Known issues
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
```

- [ ] **Step 2: Commit**

```bash
git add src/harness_claude.py
git commit -m "feat: Claude Code entry point for harness context injection"
```

---

### Task 20: Integration — start script and docker compose

**Files:**
- Create: `run.py`
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create run.py**

```python
#!/usr/bin/env python3
"""Start xx-harness web server."""
import uvicorn
from src.config import WEB_PORT

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=WEB_PORT, reload=True)
```

- [ ] **Step 2: Create Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git
COPY pyproject.toml .
RUN pip install -e .
COPY src/ src/
COPY run.py .
EXPOSE 8720
CMD ["python", "run.py"]
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
services:
  harness:
    build: .
    ports: ["8720:8720"]
    volumes:
      - harness_data:/root/.xx-harness
      - ./src:/app/src
    environment:
      - XX_HARNESS_HOME=/root/.xx-harness

volumes:
  harness_data:
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add run.py Dockerfile docker-compose.yml
git commit -m "feat: startup script and Docker deployment"
```

---

## Spec Coverage Check

| Spec Section | Covered By |
|---|---|
| 2. Core Architecture | Tasks 1, 10, 11 |
| 4.0 Task Types | Tasks 4 (models), 14 (seed), 17 (frontend) |
| 4.1-4.3 Data Models | Tasks 2-5 (adapter, schema, models, repos) |
| 5. Workspace Management | Task 6 (workspace), Task 10 (orchestrator integration) |
| 6. Skills Integration | Tasks 7 (node skill field), 16 (skill config in workflow editor) |
| 7. DAG Orchestration | Tasks 7 (dag parser), 10 (orchestrator), 18 (DAGView) |
| 8. Context Passing | Task 8 (context assembler), Task 19 (CLAUDE.md entry) |
| 9. Learning Loop | Tasks 5 (KnownIssue repo), 14 (issues API routes) |
| 10. Two Entry Points | Tasks 13 (web start task), 19 (Claude Code entry) |
| 11. Workflow Selection | Tasks 10 (auto-select), 17 (manual select in TaskCreate) |
| 12. MVP Scope | All tasks above |

**Self-Review:**
- No placeholders, TBDs, or TODOs
- All types consistent across tasks
- All spec requirements have corresponding tasks
- Each task has concrete code and expected test output
