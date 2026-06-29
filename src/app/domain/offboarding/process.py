from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.offboarding import (
        DossierId,
        EmployeeId,
        InterviewId,
        ManagerId,
        OffboardingProcessId,
    )
    from app.domain.offboarding.state import OffboardingProcessState


class OffboardingProcess:
    __id: OffboardingProcessId
    __state: OffboardingProcessState
    __employee_id: EmployeeId
    __manager_id: ManagerId
    __created_at: datetime
    __interview_id: InterviewId | None
    __dossier_id: DossierId | None

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
        self.__id = process_id
        self.__state = state
        self.__employee_id = employee_id
        self.__manager_id = manager_id
        self.__created_at = created_at
        self.__interview_id = interview_id
        self.__dossier_id = dossier_id

    @property
    def process_id(self) -> OffboardingProcessId:
        return self.__id

    @process_id.setter
    def process_id(self, process_id: OffboardingProcessId):
        self.__id = process_id

    @property
    def state(self) -> OffboardingProcessState:
        return self.__state

    @property
    def employee_id(self) -> EmployeeId:
        return self.__employee_id

    @employee_id.setter
    def employee_id(self, employee_id: EmployeeId):
        self.__employee_id = employee_id

    @property
    def manager_id(self) -> ManagerId:
        return self.__manager_id

    @manager_id.setter
    def manager_id(self, manager_id: ManagerId):
        self.__manager_id = manager_id

    @property
    def created_at(self) -> datetime:
        return self.__created_at

    @created_at.setter
    def created_at(self, created_at: datetime):
        self.__created_at = created_at

    @property
    def interview_id(self) -> InterviewId | None:
        return self.__interview_id

    @interview_id.setter
    def interview_id(self, interview_id: InterviewId | None):
        self.__interview_id = interview_id

    @property
    def dossier_id(self) -> DossierId | None:
        return self.__dossier_id

    @dossier_id.setter
    def dossier_id(self, dossier_id: DossierId | None):
        self.__dossier_id = dossier_id

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
