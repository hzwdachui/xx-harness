from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any

from src.db.adapter import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
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
        self._conn.execute("BEGIN")
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
