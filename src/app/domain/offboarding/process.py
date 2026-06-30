"""OffboardingProcess aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.base_process import Process

if TYPE_CHECKING:
    from app.domain.enums import OffboardingProcessStateEnum
    from app.domain.offboarding import (
        DossierId,
        EmployeeId,
        InterviewId,
        ManagerId,
        OffboardingProcessId,
    )
    from app.domain.offboarding.state import OffboardingProcessState


class OffboardingProcess(Process):
    """Aggregate root representing an employee offboarding process.

    Owns the lifecycle state machine and references to its Interview and Dossier by ID.
    """

    __id: OffboardingProcessId
    __state: OffboardingProcessState

    def __init__(
            self,
            process_id: OffboardingProcessId,
            state: OffboardingProcessState,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            created_at: datetime,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
    ) -> None:
        """Initialize the offboarding process with all its attributes.

        Args:
            process_id: Unique identifier for this offboarding process.
            state: Initial state of the process (typically NotStartedState).
            employee_id: ID of the employee being offboarded.
            manager_id: ID of the manager overseeing the offboarding.
            created_at: Timestamp when the process was created.
            interview_id: ID of the associated interview, if any. Defaults to None.
            dossier_id: ID of the associated dossier, if any. Defaults to None.
        """
        super().__init__(process_id, employee_id, manager_id, created_at, interview_id, dossier_id)
        self.__id = process_id
        self.__state = state

    @property
    def process_id(self) -> OffboardingProcessId:
        """The unique identifier of this offboarding process."""
        return self.__id

    @process_id.setter
    def process_id(self, process_id: OffboardingProcessId):
        """Set the process identifier."""
        self.__id = process_id

    @property
    def state(self) -> OffboardingProcessState:
        """The current state object of this offboarding process."""
        return self.__state

    @property
    def state_value(self) -> OffboardingProcessStateEnum:
        """The current state as an enum value."""
        return self.__state.get_state()

    def start(self) -> OffboardingProcessState:
        """
        Start the offboarding process.

        Returns:
            OffboardingProcessState: The new state of the offboarding process after starting.

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.start()
        self.__state = new_state
        return new_state

    def submit_for_review(self) -> OffboardingProcessState:
        """
        Submit the offboarding process for review.

        Returns:
            OffboardingProcessState: The new state of the offboarding process after submission.

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.submit_for_review()
        self.__state = new_state
        return new_state

    def complete(self) -> OffboardingProcessState:
        """
        Complete the offboarding process.

        Returns:
            OffboardingProcessState: The new state of the offboarding process after completing.

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.complete()
        self.__state = new_state
        return new_state

    def cancel(self) -> OffboardingProcessState:
        """
        Cancel the offboarding process.

        Returns:
            OffboardingProcessState: The new state after cancellation.

        Raises:
            InvalidOffboardingProcessStateTransitionError: If the transition is invalid.
        """
        new_state = self.__state.cancel()
        self.__state = new_state
        return new_state
