from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.base_process import Process
    from app.domain.offboarding import (
        DossierId,
        EmployeeId,
        InterviewId,
        ManagerId,
        OffboardingProcessId,
    )
    from app.domain.offboarding.state import OffboardingProcessState


class OffboardingProcess(Process):
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
        super().__init__(process_id, employee_id, manager_id, created_at, interview_id, dossier_id)
        self.__state = state

    @property
    def process_id(self) -> OffboardingProcessId:
        return self.__id

    @process_id.setter
    def process_id(self, process_id: OffboardingProcessId):
        self.__id = process_id

    @property
    def state(self) -> OffboardingProcessState:
        return self.__state

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
