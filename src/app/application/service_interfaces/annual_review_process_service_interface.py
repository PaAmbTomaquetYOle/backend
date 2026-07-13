"""Abstract contract for the annual review process service."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.application.service_interfaces.process_service_interface import IProcessService
from app.domain import (
    AnnualReviewProcess,
    AnnualReviewProcessId,
    AnnualReviewProcessStateEnum,
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
)


class IAnnualReviewProcessService(IProcessService, ABC):
    """Interface for annual review process lifecycle management.

    Extends IProcessService with annual-review-specific state transitions.
    Implemented by AnnualReviewProcessService.
    """

    @abstractmethod
    async def create_process(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> AnnualReviewProcess:
        """Create a new annual review process in NOT_STARTED state.

        Args:
            employee_id: Identifier of the employee/volunteer being reviewed.
            manager_id: Identifier of the manager overseeing the review.
            employee_name: Display name of the employee, if known. Defaults to None.
            manager_name: Display name of the manager, if known. Defaults to None.

        Returns:
            The newly created AnnualReviewProcess.
        """
        ...

    @abstractmethod
    async def get_process(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Retrieve an annual review process by ID.

        Args:
            process_id: Identifier of the process to retrieve.

        Returns:
            The matching AnnualReviewProcess.

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
            state: AnnualReviewProcessStateEnum | None = None,
    ) -> Iterable[AnnualReviewProcess]:
        """Return all processes matching the provided filters.

        All filters are optional and combined with AND logic when provided.

        Args:
            employee_id: Filter by employee. Defaults to None.
            manager_id: Filter by manager. Defaults to None.
            interview_id: Filter by associated interview. Defaults to None.
            dossier_id: Filter by associated dossier. Defaults to None.
            state: Filter by lifecycle state. Defaults to None.

        Returns:
            Iterable of AnnualReviewProcess objects matching all specified filters.
        """
        ...

    @abstractmethod
    async def start_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS.

        Args:
            process_id: Identifier of the process to start.

        Returns:
            The updated AnnualReviewProcess in IN_PROGRESS state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidAnnualReviewProcessStateTransitionError: If the process is not in
                NOT_STARTED state.
        """
        ...

    @abstractmethod
    async def cancel_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Transition the process to CANCELLED.

        Args:
            process_id: Identifier of the process to cancel.

        Returns:
            The updated AnnualReviewProcess in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidAnnualReviewProcessStateTransitionError: If the process is already in
                a terminal state.
        """
        ...

    @abstractmethod
    async def submit_for_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Transition the process from IN_PROGRESS to PENDING_REVISION.

        Args:
            process_id: Identifier of the process to submit.

        Returns:
            The updated AnnualReviewProcess in PENDING_REVISION state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidAnnualReviewProcessStateTransitionError: If the process is not in
                IN_PROGRESS state.
        """
        ...

    @abstractmethod
    async def complete_review(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess:
        """Transition the process from PENDING_REVISION to FINISHED.

        Args:
            process_id: Identifier of the process to complete.

        Returns:
            The updated AnnualReviewProcess in FINISHED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidAnnualReviewProcessStateTransitionError: If the process is not in
                PENDING_REVISION state.
        """
        ...

    @abstractmethod
    async def delete_process(self, process_id: AnnualReviewProcessId) -> None:
        """Permanently delete the process record.

        Args:
            process_id: Identifier of the process to delete.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        ...
