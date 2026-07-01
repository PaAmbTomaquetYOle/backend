from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.enums.process_state import ProcessStateEnum
    from app.domain.offboarding.id import (
        DossierId,
        EmployeeId,
        InterviewId,
        ManagerId,
        ProcessId,
    )


class Process(ABC):
    """
    Abstract base class for all other processes.
    """
    __id: ProcessId
    __employee_id: EmployeeId
    __manager_id: ManagerId
    __created_at: datetime
    __interview_id: InterviewId | None
    __dossier_id: DossierId | None
    __employee_name: str | None
    __manager_name: str | None

    def __init__(
            self,
            process_id: ProcessId,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            created_at: datetime,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> None:
        """Initialize the process with its identifying attributes.

        Args:
            process_id: Unique identifier for this process.
            employee_id: ID of the employee the process belongs to.
            manager_id: ID of the manager responsible for the process.
            created_at: Timestamp when the process was created.
            interview_id: ID of the associated interview, if any. Defaults to None.
            dossier_id: ID of the associated dossier, if any. Defaults to None.
            employee_name: Display name of the employee, if known. Defaults to None.
            manager_name: Display name of the manager, if known. Defaults to None.
        """
        self.__id = process_id
        self.__employee_id = employee_id
        self.__manager_id = manager_id
        self.__created_at = created_at
        self.__interview_id = interview_id
        self.__dossier_id = dossier_id
        self.__employee_name = employee_name
        self.__manager_name = manager_name

    @property
    def process_id(self) -> ProcessId:
        """The unique identifier of this process."""
        return self.__id

    @process_id.setter
    def process_id(self, process_id: ProcessId) -> None:
        """Set the process identifier."""
        self.__id = process_id

    @property
    def employee_id(self) -> EmployeeId:
        """The ID of the employee this process belongs to."""
        return self.__employee_id

    @employee_id.setter
    def employee_id(self, employee_id: EmployeeId):
        """Set the employee identifier."""
        self.__employee_id = employee_id

    @property
    def manager_id(self) -> ManagerId:
        """The ID of the manager responsible for this process."""
        return self.__manager_id

    @manager_id.setter
    def manager_id(self, manager_id: ManagerId):
        """Set the manager identifier."""
        self.__manager_id = manager_id

    @property
    def created_at(self) -> datetime:
        """Timestamp when the process was created."""
        return self.__created_at

    @created_at.setter
    def created_at(self, created_at: datetime):
        """Set the creation timestamp."""
        self.__created_at = created_at

    @property
    def interview_id(self) -> InterviewId | None:
        """The ID of the associated interview, or None if not yet created."""
        return self.__interview_id

    @interview_id.setter
    def interview_id(self, interview_id: InterviewId | None):
        """Set the associated interview ID."""
        self.__interview_id = interview_id

    @property
    def dossier_id(self) -> DossierId | None:
        """The ID of the associated dossier, or None if not yet created."""
        return self.__dossier_id

    @dossier_id.setter
    def dossier_id(self, dossier_id: DossierId | None):
        """Set the associated dossier ID."""
        self.__dossier_id = dossier_id

    @property
    def employee_name(self) -> str | None:
        """The display name of the employee, or None if unknown."""
        return self.__employee_name

    @employee_name.setter
    def employee_name(self, employee_name: str | None):
        """Set the employee display name."""
        self.__employee_name = employee_name

    @property
    def manager_name(self) -> str | None:
        """The display name of the manager, or None if unknown."""
        return self.__manager_name

    @manager_name.setter
    def manager_name(self, manager_name: str | None):
        """Set the manager display name."""
        self.__manager_name = manager_name

    @property
    @abstractmethod
    def state_value(self) -> ProcessStateEnum:
        """The current state of this process as an enum value."""
        pass