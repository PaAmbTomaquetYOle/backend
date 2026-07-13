"""SQLModel engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel

_engine: AsyncEngine | None = None


def init_engine(url: str) -> None:
    """Initialize the SQLModel engine with the given database URL.

    Args:
        url: SQLAlchemy-compatible async database URL string.
    """
    global _engine
    _engine = create_async_engine(url)


def get_engine() -> AsyncEngine:
    """Return the active SQLModel engine.

    Returns:
        AsyncEngine: The initialized SQLAlchemy async engine.

    Raises:
        RuntimeError: If the engine has not been initialized yet.
    """
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a SQLModel session for the current request, closing it when done.

    Yields:
        AsyncSession: An active database session.
    """
    async with AsyncSession(get_engine()) as session:
        yield session


async def create_db_and_tables() -> None:
    """Create all SQLModel-registered tables in the database if they do not already exist.

    Also creates the Postgres GIN full-text search index on ``sops.content``
    when running against Postgres — this index cannot be declared on the
    SQLModel table directly because SQLite (used in tests) has no
    to_tsvector/GIN support.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        if engine.dialect.name == "postgresql":
            from app.infrastructure.persistence.models.sop import SOPS_CONTENT_FTS_INDEX_SQL

            await conn.execute(text(SOPS_CONTENT_FTS_INDEX_SQL))
