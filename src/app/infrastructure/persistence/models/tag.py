"""SQLModel persistence models for SOP tags (many-to-many)."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, SQLModel


class TagModel(SQLModel, table=True):
    """A named tag, shared across SOPs."""

    __tablename__ = "tags"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, unique=True, index=True, max_length=64)


class SopTagLink(SQLModel, table=True):
    """Many-to-many link table between SOPs and tags."""

    __tablename__ = "sop_tags"

    sop_id: uuid.UUID = Field(
        sa_column=Column(Uuid, ForeignKey("sops.id", ondelete="CASCADE"), primary_key=True)
    )
    tag_id: uuid.UUID = Field(
        sa_column=Column(Uuid, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    )
