"""MonthlyReviewProcess aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.base_process import Process

if TYPE_CHECKING:
    from app.domain.enums import MonthlyReviewProcessStateEnum
    from app.domain.monthly_review.id import MonthlyReviewProcessId
    from app.domain.monthly_review.state import MonthlyReviewProcessState
    from app.domain.offboarding import DossierId, EmployeeId, InterviewId, ManagerId


class MonthlyReviewProcess(Process):
    """Aggregate root representing a monthly knowledge-retention review process.

    A lightweight, recurring review focused on an employee/volunteer's recent tasks.
    Owns the lifecycle state machine and references to its Interview and Dossier by ID.
    """

    __id: MonthlyReviewProcessId
    __state: MonthlyReviewProcessState

    def __init__(
            self,
            process_id: MonthlyReviewProcessId,
            state: MonthlyReviewProcessState,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            created_at: datetime,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> None:
        """Initialize the monthly review process with all its attributes.

        Args:
            process_id: Unique identifier for this monthly review process.
            state: Initial state of the process (typically NotStartedState).
            employee_id: ID of the employee/volunteer being reviewed.
            manager_id: ID of the manager overseeing the review.
            created_at: Timestamp when the process was created.
            interview_id: ID of the associated interview, if any. Defaults to None.
            dossier_id: ID of the associated dossier, if any. Defaults to None.
            employee_name: Display name of the employee, if known. Defaults to None.
            manager_name: Display name of the manager, if known. Defaults to None.
        """
        super().__init__(
            process_id, employee_id, manager_id, created_at, interview_id, dossier_id,
            employee_name, manager_name,
        )
        self.__id = process_id
        self.__state = state

    @property
    def process_id(self) -> MonthlyReviewProcessId:
        """The unique identifier of this monthly review process."""
        return self.__id

    @process_id.setter
    def process_id(self, process_id: MonthlyReviewProcessId):
        """Set the process identifier."""
        self.__id = process_id

    @property
    def state(self) -> MonthlyReviewProcessState:
        """The current state object of this monthly review process."""
        return self.__state

    @property
    def state_value(self) -> MonthlyReviewProcessStateEnum:
        """The current state as an enum value."""
        return self.__state.get_state()

    def start(self) -> MonthlyReviewProcessState:
        """
        Start the monthly review process.

        Returns:
            MonthlyReviewProcessState: The new state of the process after starting.

        Raises:
            InvalidMonthlyReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.start()
        self.__state = new_state
        return new_state

    def complete(self) -> MonthlyReviewProcessState:
        """
        Complete the monthly review process.

        Returns:
            MonthlyReviewProcessState: The new state of the process after completing.

        Raises:
            InvalidMonthlyReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.complete()
        self.__state = new_state
        return new_state

    def cancel(self) -> MonthlyReviewProcessState:
        """
        Cancel the monthly review process.

        Returns:
            MonthlyReviewProcessState: The new state after cancellation.

        Raises:
            InvalidMonthlyReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.cancel()
        self.__state = new_state
        return new_state
