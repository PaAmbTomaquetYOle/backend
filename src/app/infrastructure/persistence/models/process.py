"""SQLModel base model for the process hierarchy (class table inheritance)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class ProcessModel(SQLModel, table=True):
    """SQLModel base for the process class-table inheritance hierarchy.

    Not persisted directly; subclassed by OffboardingProcessModel.
    """

    __tablename__ = "processes"
    __table_args__ = (
        CheckConstraint(
            "type IN ('offboarding')",
            name="ck_processes_type",
        ),
    )

    id: uuid.UUID = Field(primary_key=True)
    type: str = Field(nullable=False)
    employee_id: uuid.UUID = Field(index=True, nullable=False)
    manager_id: uuid.UUID = Field(nullable=False)
    created_at: datetime = Field(nullable=False)
