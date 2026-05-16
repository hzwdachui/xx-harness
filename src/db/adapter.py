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

    @abstractmethod
    @contextmanager
    def transaction(self): ...
