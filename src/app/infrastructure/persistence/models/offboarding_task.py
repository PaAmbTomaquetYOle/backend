"""SQLModel persistence model for offboarding tasks (SA-18)."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.enums import TaskSourceEnum
from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask


class OffboardingTaskModel(SQLModel, table=True):
    """SQLModel persistence model for a single extracted Jira/Trello task.

    Standalone child table keyed by process_id — full-set replace semantics (see
    OffboardingTaskRepository.replace_for_process), so there is no independent lifecycle to
    guard, unlike SopCandidate. Unique on (process_id, task_id, source) since that triple is
    the natural key slack-agent already uses to identify a task.
    """

    __tablename__ = "offboarding_tasks"
    __table_args__ = (
        sa.UniqueConstraint(
            "process_id", "task_id", "source", name="uq_offboarding_tasks_process_task_source"
        ),
        sa.CheckConstraint("source IN ('jira','trello')", name="ck_offboarding_tasks_source"),
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    process_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("offboarding_processes.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    task_id: str = Field(nullable=False, max_length=128)
    title: str = Field(nullable=False)
    source: str = Field(nullable=False, max_length=16)
    status: str = Field(nullable=False, max_length=64)
    url: str | None = Field(default=None)
    description: str | None = Field(default=None)

    @classmethod
    def from_domain(cls, task: OffboardingTask) -> OffboardingTaskModel:
        """Create an OffboardingTaskModel from a domain OffboardingTask.

        Args:
            task: The domain task to persist.

        Returns:
            OffboardingTaskModel: The corresponding persistence model.
        """
        return cls(
            process_id=task.process_id.get_id(),
            task_id=task.task_id,
            title=task.title,
            source=task.source.value,
            status=task.status,
            url=task.url,
            description=task.description,
        )

    def to_domain(self) -> OffboardingTask:
        """Reconstruct a domain OffboardingTask from this model.

        Returns:
            OffboardingTask: The reconstructed domain aggregate.
        """
        return OffboardingTask(
            process_id=OffboardingProcessId(self.process_id),
            task_id=self.task_id,
            title=self.title,
            source=TaskSourceEnum(self.source),
            status=self.status,
            url=self.url,
            description=self.description,
        )
