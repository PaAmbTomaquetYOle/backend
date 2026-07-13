"""SQLModel persistence model for monthly review processes (class table inheritance)."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.monthly_review.state.base import MonthlyReviewProcessState
from app.domain.monthly_review.state.cancelled import CancelledState
from app.domain.monthly_review.state.finished import FinishedState
from app.domain.monthly_review.state.in_progress import InProgressState
from app.domain.monthly_review.state.not_started import NotStartedState

_STATE_FACTORIES: dict[str, type[MonthlyReviewProcessState]] = {
    MonthlyReviewProcessStateEnum.NOT_STARTED.value: NotStartedState,
    MonthlyReviewProcessStateEnum.IN_PROGRESS.value: InProgressState,
    MonthlyReviewProcessStateEnum.FINISHED.value: FinishedState,
    MonthlyReviewProcessStateEnum.CANCELLED.value: CancelledState,
}


class MonthlyReviewProcessModel(SQLModel, table=True):
    """SQLModel persistence model for monthly review processes.

    Maps the MonthlyReviewProcess aggregate to the database via class-table inheritance.
    """

    __tablename__ = "monthly_review_processes"
    __table_args__ = (
        CheckConstraint(
            "state IN ('not_started','in_progress','finished','cancelled')",
            name="ck_monthly_review_processes_state",
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

    def get_state_factory(self) -> MonthlyReviewProcessState:
        """Return the domain state object corresponding to the persisted state string.

        Returns:
            MonthlyReviewProcessState: The matching concrete state instance.

        Raises:
            ValueError: If the stored state value is unrecognized.
        """
        return _STATE_FACTORIES[self.state]()
