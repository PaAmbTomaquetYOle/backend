"""SQLModel persistence model for offboarding processes (class table inheritance at SQL level)."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.finished import FinishedState
from app.domain.offboarding.state.in_progress import InProgressState
from app.domain.offboarding.state.not_started import NotStartedState
from app.domain.offboarding.state.pending_revision import PendingRevisionState

_STATE_FACTORIES: dict[str, type[OffboardingProcessState]] = {
    OffboardingProcessStateEnum.NOT_STARTED.value: NotStartedState,
    OffboardingProcessStateEnum.IN_PROGRESS.value: InProgressState,
    OffboardingProcessStateEnum.PENDING_REVISION.value: PendingRevisionState,
    OffboardingProcessStateEnum.FINISHED.value: FinishedState,
    OffboardingProcessStateEnum.CANCELLED.value: CancelledState,
}


class OffboardingProcessModel(SQLModel, table=True):
    __tablename__ = "offboarding_processes"
    __table_args__ = (
        CheckConstraint(
            "state IN ('not_started','in_progress','pending_revision','finished','cancelled')",
            name="ck_offboarding_processes_state",
        ),
    )

    id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("processes.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    state: str = Field(nullable=False)

    def get_state_factory(self) -> OffboardingProcessState:
        return _STATE_FACTORIES[self.state]()
