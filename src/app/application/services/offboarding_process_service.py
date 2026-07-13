"""Concrete implementation of the offboarding process service."""

from collections.abc import Iterable
from datetime import UTC, datetime

from app.application.ports.offboarding_process import IOffboardingProcessRepository
from app.application.service_interfaces.offboarding_process_service_interface import (
    IOffboardingProcessService,
)
from app.domain import (
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
    NotStartedState,
    OffboardingProcess,
    OffboardingProcessId,
    ProcessId,
)
from app.domain.enums import ProcessStateEnum
from app.domain.exceptions.offboarding import ProcessNotFoundError


class OffboardingProcessService(IOffboardingProcessService):
    """Orchestrates offboarding process lifecycle operations.

    Delegates persistence to IOffboardingProcessRepository. Applies in-memory
    filtering when multiple repository indexes are not available.
    """

    def __init__(self, repo: IOffboardingProcessRepository) -> None:
        """Set up the service with a repository.

        Args:
            repo: The repository used to persist and retrieve offboarding processes.
        """
        self._repo = repo

    async def create_process(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> OffboardingProcess:
        """Create and persist a new offboarding process in NOT_STARTED state.

        Args:
            employee_id: Identifier of the employee being offboarded.
            manager_id: Identifier of the manager responsible for the process.
            employee_name: Display name of the employee, if known. Defaults to None.
            manager_name: Display name of the manager, if known. Defaults to None.

        Returns:
            The newly created and persisted OffboardingProcess.
        """
        process = OffboardingProcess(
            process_id=OffboardingProcessId(),
            state=NotStartedState(),
            employee_id=employee_id,
            manager_id=manager_id,
            created_at=datetime.now(UTC),
            employee_name=employee_name,
            manager_name=manager_name,
        )
        await self._repo.save(process)
        return process

    async def get_process(self, process_id: ProcessId) -> OffboardingProcess:
        """Retrieve an offboarding process by ID.

        Args:
            process_id: Identifier of the process to retrieve.

        Returns:
            The matching OffboardingProcess.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        process = await self._repo.find_by_id(OffboardingProcessId(process_id.get_id()))
        if process is None:
            raise ProcessNotFoundError(str(process_id.get_id()))
        return process

    async def get_filtered_processes(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            state: ProcessStateEnum | None = None,
    ) -> Iterable[OffboardingProcess]:
        """Return all processes matching the provided filters.

        Uses the employee index when employee_id is provided; otherwise loads all
        processes and applies remaining filters in memory.

        Args:
            employee_id: Filter by employee. Defaults to None.
            manager_id: Filter by manager. Defaults to None.
            interview_id: Filter by associated interview. Defaults to None (unused in v1).
            dossier_id: Filter by associated dossier. Defaults to None (unused in v1).
            state: Filter by lifecycle state. Defaults to None.

        Returns:
            Iterable of OffboardingProcess objects matching all specified filters.
        """
        if employee_id is not None:
            processes = await self._repo.find_by_employee_id(employee_id)
        else:
            processes = await self._repo.find_all()
        if manager_id is not None:
            processes = [p for p in processes if p.manager_id.get_id() == manager_id.get_id()]
        if state is not None:
            processes = [p for p in processes if p.state_value == state]
        return processes

    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS and persist.

        Args:
            process_id: Identifier of the process to start.

        Returns:
            The updated OffboardingProcess in IN_PROGRESS state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in
                NOT_STARTED state.
        """
        process = await self.get_process(process_id)
        process.start()
        await self._repo.save(process)
        return process

    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process to CANCELLED and persist.

        Args:
            process_id: Identifier of the process to cancel.

        Returns:
            The updated OffboardingProcess in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is already in
                a terminal state.
        """
        process = await self.get_process(process_id)
        process.cancel()
        await self._repo.save(process)
        return process

    async def submit_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from IN_PROGRESS to PENDING_REVISION and persist.

        Args:
            process_id: Identifier of the process to submit.

        Returns:
            The updated OffboardingProcess in PENDING_REVISION state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in
                IN_PROGRESS state.
        """
        process = await self.get_process(process_id)
        process.submit_for_review()
        await self._repo.save(process)
        return process

    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from PENDING_REVISION to FINISHED and persist.

        Args:
            process_id: Identifier of the process to complete.

        Returns:
            The updated OffboardingProcess in FINISHED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in
                PENDING_REVISION state.
        """
        process = await self.get_process(process_id)
        process.complete()
        await self._repo.save(process)
        return process

    async def delete_process(self, process_id: OffboardingProcessId) -> None:
        """Permanently delete the process record.

        Verifies the process exists before deleting.

        Args:
            process_id: Identifier of the process to delete.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        await self.get_process(process_id)
        await self._repo.delete(process_id)
