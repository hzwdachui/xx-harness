from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data


def test_schema_creation(tmp_path):
    db = SQLiteAdapter(str(tmp_path / "test.db"))
    create_schema(db)
    tables = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
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
