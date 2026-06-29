from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.domain import (
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
    Process,
    ProcessId,
)
from app.domain.enums import ProcessStateEnum


class IProcessService(ABC):
    """
    Interface for all process services.
    """

    @abstractmethod
    async def create_process(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            interview_id: InterviewId,
            dossier_id: DossierId
    ) -> Process:
        """
        Create a new process object.

        Args:
            employee_id: Employee id
            manager_id: Manager id
            interview_id: Interview id
            dossier_id: Dossier id

        Returns:
            Process object
        """

    @abstractmethod
    async def get_process(self, process_id: ProcessId) -> Process:
        """
        Get a process object.

        Args:
            process_id: Process id

        Returns:
            Process object
        """

    @abstractmethod
    async def get_filtered_processes(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            state: ProcessStateEnum | None = None,
    ) -> Iterable[Process]:
        """
        Get all processes filtered by the given parameters.

        Args:
            employee_id: Employee id
            manager_id: Manager id
            interview_id: Interview id
            dossier_id: Dossier id
            state: Process state

        Returns:
            Iterable of Process objects
        """
