"""SQLModel persistence model for annual review processes (class table inheritance at SQL level)."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.annual_review.state.base import AnnualReviewProcessState
from app.domain.annual_review.state.cancelled import CancelledState
from app.domain.annual_review.state.finished import FinishedState
from app.domain.annual_review.state.in_progress import InProgressState
from app.domain.annual_review.state.not_started import NotStartedState
from app.domain.annual_review.state.pending_revision import PendingRevisionState
from app.domain.enums import AnnualReviewProcessStateEnum

_STATE_FACTORIES: dict[str, type[AnnualReviewProcessState]] = {
    AnnualReviewProcessStateEnum.NOT_STARTED.value: NotStartedState,
    AnnualReviewProcessStateEnum.IN_PROGRESS.value: InProgressState,
    AnnualReviewProcessStateEnum.PENDING_REVISION.value: PendingRevisionState,
    AnnualReviewProcessStateEnum.FINISHED.value: FinishedState,
    AnnualReviewProcessStateEnum.CANCELLED.value: CancelledState,
}


class AnnualReviewProcessModel(SQLModel, table=True):
    """SQLModel persistence model for annual review processes.

    Maps the AnnualReviewProcess aggregate to the database via class-table inheritance.
    """

    __tablename__ = "annual_review_processes"
    __table_args__ = (
        CheckConstraint(
            "state IN ('not_started','in_progress','pending_revision','finished','cancelled')",
            name="ck_annual_review_processes_state",
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

    def get_state_factory(self) -> AnnualReviewProcessState:
        """Return the domain state object corresponding to the persisted state string.

        Returns:
            AnnualReviewProcessState: The matching concrete state instance.

        Raises:
            ValueError: If the stored state value is unrecognized.
        """
        return _STATE_FACTORIES[self.state]()
