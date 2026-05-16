"""Contract test for DatabaseAdapter -- run against any adapter implementation."""
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
