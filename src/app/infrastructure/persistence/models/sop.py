"""SQLModel persistence model for SOPs, with a full-text search index on title+content."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

# The Postgres GIN full-text index on `title || ' ' || content` (to_tsvector)
# is created separately, outside SQLModel metadata, by the Alembic baseline
# migration (production) and by
# `infrastructure.persistence.database.create_db_and_tables` (SQLite-backed
# test fixtures have no to_tsvector/GIN support, so it cannot be a declarative
# Index here without breaking the SQLite-backed test suite).
SOPS_CONTENT_FTS_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS ix_sops_content_fts "
    "ON sops USING gin (to_tsvector('english', title || ' ' || content))"
)


class SopModel(SQLModel, table=True):
    """SQLModel persistence model for a Standard Operating Procedure.

    Standalone aggregate — unlike OffboardingProcessModel, it does not
    participate in the ``processes`` class-table hierarchy, since a SOP has no
    lifecycle state machine.
    """

    __tablename__ = "sops"

    id: uuid.UUID = Field(primary_key=True)
    title: str = Field(nullable=False, max_length=200)
    content: str = Field(nullable=False)
    author: str = Field(nullable=False, max_length=64)
    origin_channel: str = Field(nullable=False, max_length=64)
    version: int = Field(nullable=False, default=1)
    created_at: datetime = Field(nullable=False)
    updated_at: datetime = Field(nullable=False)
    deleted_at: datetime | None = Field(default=None)
