"""AnnualReviewProcess aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.base_process import Process

if TYPE_CHECKING:
    from app.domain.annual_review.id import AnnualReviewProcessId
    from app.domain.annual_review.state import AnnualReviewProcessState
    from app.domain.enums import AnnualReviewProcessStateEnum
    from app.domain.offboarding import DossierId, EmployeeId, InterviewId, ManagerId


class AnnualReviewProcess(Process):
    """Aggregate root representing an annual knowledge-retention review process.

    An exhaustive, recurring review focused on all of an employee/volunteer's
    accumulated knowledge. Owns the lifecycle state machine and references to its
    Interview and Dossier by ID.
    """

    __id: AnnualReviewProcessId
    __state: AnnualReviewProcessState

    def __init__(
            self,
            process_id: AnnualReviewProcessId,
            state: AnnualReviewProcessState,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            created_at: datetime,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> None:
        """Initialize the annual review process with all its attributes.

        Args:
            process_id: Unique identifier for this annual review process.
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
    def process_id(self) -> AnnualReviewProcessId:
        """The unique identifier of this annual review process."""
        return self.__id

    @process_id.setter
    def process_id(self, process_id: AnnualReviewProcessId):
        """Set the process identifier."""
        self.__id = process_id

    @property
    def state(self) -> AnnualReviewProcessState:
        """The current state object of this annual review process."""
        return self.__state

    @property
    def state_value(self) -> AnnualReviewProcessStateEnum:
        """The current state as an enum value."""
        return self.__state.get_state()

    def start(self) -> AnnualReviewProcessState:
        """
        Start the annual review process.

        Returns:
            AnnualReviewProcessState: The new state of the process after starting.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.start()
        self.__state = new_state
        return new_state

    def submit_for_review(self) -> AnnualReviewProcessState:
        """
        Submit the annual review process for review.

        Returns:
            AnnualReviewProcessState: The new state of the process after submission.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.submit_for_review()
        self.__state = new_state
        return new_state

    def complete(self) -> AnnualReviewProcessState:
        """
        Complete the annual review process.

        Returns:
            AnnualReviewProcessState: The new state of the process after completing.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.complete()
        self.__state = new_state
        return new_state

    def cancel(self) -> AnnualReviewProcessState:
        """
        Cancel the annual review process.

        Returns:
            AnnualReviewProcessState: The new state after cancellation.

        Raises:
            InvalidAnnualReviewProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.cancel()
        self.__state = new_state
        return new_state
