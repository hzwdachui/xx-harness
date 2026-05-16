import pytest
import sqlite3
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_db():
    """Temporary SQLite database fixture.
    Will be upgraded to use DatabaseAdapter once db layer is built (Task 2-3)."""
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()


@pytest.fixture
def tmp_workspace() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
