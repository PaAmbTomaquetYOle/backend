"""SQLModel engine and session management."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

_engine: Engine | None = None


def init_engine(url: str) -> None:
    global _engine
    _engine = create_engine(url)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(get_engine())
