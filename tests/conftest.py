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
