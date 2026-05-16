import pytest
import tempfile
from pathlib import Path

from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data


@pytest.fixture
def tmp_db():
    """Temporary SQLite database fixture backed by SQLiteAdapter."""
    with tempfile.TemporaryDirectory() as d:
        db_path = Path(d) / "test.db"
        db = SQLiteAdapter(str(db_path))
        create_schema(db)
        seed_data(db)
        yield db


@pytest.fixture
def tmp_workspace() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
