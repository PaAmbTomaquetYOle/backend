"""SQLModel engine and session management."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

_engine: Engine | None = None


def init_engine(url: str) -> None:
    """Initialize the SQLModel engine with the given database URL.

    Args:
        url: SQLAlchemy-compatible database URL string.
    """
    global _engine
    _engine = create_engine(url)


def get_engine() -> Engine:
    """Return the active SQLModel engine.

    Returns:
        Engine: The initialized SQLAlchemy engine.

    Raises:
        RuntimeError: If the engine has not been initialized yet.
    """
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session for the current request, closing it when done.

    Yields:
        Session: An active database session.
    """
    with Session(get_engine()) as session:
        yield session


def create_db_and_tables() -> None:
    """Create all SQLModel-registered tables in the database if they do not already exist."""
    SQLModel.metadata.create_all(get_engine())
