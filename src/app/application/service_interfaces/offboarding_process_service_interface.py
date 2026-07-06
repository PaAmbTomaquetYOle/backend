"""Abstract contract for the offboarding process service."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.application.service_interfaces.process_service_interface import IProcessService
from app.domain import (
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
    OffboardingProcess,
    OffboardingProcessId,
    OffboardingProcessStateEnum,
)


class IOffboardingProcessService(IProcessService, ABC):
    """Interface for offboarding process lifecycle management.

    Extends IProcessService with offboarding-specific state transitions.
    Implemented by OffboardingProcessService.
    """

    @abstractmethod
    async def create_process(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> OffboardingProcess:
        """Create a new offboarding process in NOT_STARTED state.

        Args:
            employee_id: Identifier of the employee being offboarded.
            manager_id: Identifier of the manager responsible for the process.
            employee_name: Display name of the employee, if known. Defaults to None.
            manager_name: Display name of the manager, if known. Defaults to None.

        Returns:
            The newly created OffboardingProcess.
        """
        ...

    @abstractmethod
    async def get_process(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Retrieve an offboarding process by ID.

        Args:
            process_id: Identifier of the process to retrieve.

        Returns:
            The matching OffboardingProcess.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        ...

    @abstractmethod
    async def get_filtered_processes(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> Iterable[OffboardingProcess]:
        """Return all processes matching the provided filters.

        All filters are optional and combined with AND logic when provided.

        Args:
            employee_id: Filter by employee. Defaults to None.
            manager_id: Filter by manager. Defaults to None.
            interview_id: Filter by associated interview. Defaults to None.
            dossier_id: Filter by associated dossier. Defaults to None.
            state: Filter by lifecycle state. Defaults to None.

        Returns:
            Iterable of OffboardingProcess objects matching all specified filters.
        """
        ...

    @abstractmethod
    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS.

        Args:
            process_id: Identifier of the process to start.

        Returns:
            The updated OffboardingProcess in IN_PROGRESS state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in
                NOT_STARTED state.
        """
        ...

    @abstractmethod
    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process to CANCELLED.

        Args:
            process_id: Identifier of the process to cancel.

        Returns:
            The updated OffboardingProcess in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is already in
                a terminal state.
        """
        ...

    @abstractmethod
    async def submit_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from IN_PROGRESS to PENDING_REVISION.

        Args:
            process_id: Identifier of the process to submit.

        Returns:
            The updated OffboardingProcess in PENDING_REVISION state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in
                IN_PROGRESS state.
        """
        ...

    @abstractmethod
    async def complete_offboarding(
            self,
            process_id: OffboardingProcessId
    ) -> OffboardingProcess:
        """Transition the process from PENDING_REVISION to FINISHED.

        Args:
            process_id: Identifier of the process to complete.

        Returns:
            The updated OffboardingProcess in FINISHED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in
                PENDING_REVISION state.
        """
        ...

    @abstractmethod
    async def delete_process(self, process_id: OffboardingProcessId) -> None:
        """Permanently delete the process record.

        Args:
            process_id: Identifier of the process to delete.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        ...
