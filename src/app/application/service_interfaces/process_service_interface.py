from abc import ABC, abstractmethod

from app.domain import DossierId, EmployeeId, InterviewId, ManagerId, Process, ProcessId


class IProcessService(ABC):
    """
    Interface for process services
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