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
        ("researcher", "researcher", "探索代码库，分析结构，输出调研报告。你只有只读权限。"),
        ("planner", "planner", "基于需求和调研，产出结构化执行计划。你有只读权限和写计划权限。"),
        ("executor", "executor", "按计划实现功能，遵循所有约束规则。你有读写和 git 权限。"),
        ("reviewer", "reviewer", "审查代码变更，跑 Linter 和测试，输出问题清单。你有只读权限。"),
        ("tester", "tester", "编写和运行测试，验证功能正确性。你有读写权限。"),
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
        existing = db.fetch_one(
            "SELECT id FROM skill_mapping WHERE agent_role=? AND skill=?", [role, skill]
        )
        if not existing:
            db.execute(
                "INSERT INTO skill_mapping (agent_role, skill) VALUES (?, ?)", [role, skill]
            )
