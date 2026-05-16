from src.db.sqlite import SQLiteAdapter
from src.db.schema import create_schema, seed_data
from src.engine.orchestrator import Orchestrator
from src.config import DB_PATH

_db: SQLiteAdapter | None = None


def get_db():
    global _db
    if _db is None:
        _db = SQLiteAdapter(str(DB_PATH))
        create_schema(_db)
        seed_data(_db)
    return _db


def get_orchestrator():
    return Orchestrator(get_db())
