from __future__ import annotations

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

    def last_insert_id(self) -> int:
        row = self.fetch_one("SELECT last_insert_rowid() AS id")
        return row["id"] if row else 0

    @abstractmethod
    @contextmanager
    def transaction(self): ...
