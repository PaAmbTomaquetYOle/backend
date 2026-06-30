"""Facade service interfaces used by the HTTP routers. Split by bounded sub-domain (ISP)."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import (
    Dossier,
    DossierSection,
    EmployeeId,
    Interview,
    InterviewTurn,
    ManagerId,
    OffboardingProcess,
    OffboardingProcessId,
)
from app.domain.enums import OffboardingProcessStateEnum


class IOffboardingProcessFacade(ABC):
    """Process CRUD and lifecycle transitions. Used by the offboarding router."""

    @abstractmethod
    async def create_offboarding(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
    ) -> OffboardingProcess:
        """Create a new offboarding process in NOT_STARTED state.

        Args:
            employee_id: Identifier of the employee being offboarded.
            manager_id: Identifier of the manager responsible for the process.

        Returns:
            The newly created OffboardingProcess.
        """
        ...

    @abstractmethod
    async def get_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
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
    async def list_offboardings(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> list[OffboardingProcess]:
        """Return offboarding processes matching optional filters.

        All filters are optional and combined with AND logic when provided.

        Args:
            employee_id: Filter by employee. Defaults to None.
            manager_id: Filter by manager. Defaults to None.
            state: Filter by lifecycle state. Defaults to None.

        Returns:
            List of matching OffboardingProcess objects.
        """
        ...

    @abstractmethod
    async def delete_offboarding(self, process_id: OffboardingProcessId) -> None:
        """Delete an offboarding process by ID.

        Args:
            process_id: Identifier of the process to delete.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
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
            InvalidOffboardingProcessStateTransitionError: If the process is not in NOT_STARTED state.
        """
        ...

    @abstractmethod
    async def submit_offboarding_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from IN_PROGRESS to PENDING_REVISION.

        Args:
            process_id: Identifier of the process to submit.

        Returns:
            The updated OffboardingProcess in PENDING_REVISION state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in IN_PROGRESS state.
        """
        ...

    @abstractmethod
    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from PENDING_REVISION to FINISHED.

        Args:
            process_id: Identifier of the process to complete.

        Returns:
            The updated OffboardingProcess in FINISHED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in PENDING_REVISION state.
        """
        ...

    @abstractmethod
    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Cancel the offboarding process.

        Args:
            process_id: Identifier of the process to cancel.

        Returns:
            The updated OffboardingProcess in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is already in a terminal state.
        """
        ...


class IOffboardingInterviewFacade(ABC):
    """Interview operations scoped to an offboarding process. Used by the interview sub-router."""

    @abstractmethod
    async def upsert_interview(
            self,
            process_id: OffboardingProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Create or replace the interview for the given offboarding process.

        Verifies the process exists before acting. If no interview exists, creates one.
        If one already exists, replaces its scheduled_at and turns while preserving the
        original ID and creation timestamp.

        Args:
            process_id: Identifier of the offboarding process.
            scheduled_at: Datetime when the interview is scheduled.
            turns: Optional list of turns to attach. Defaults to None.

        Returns:
            A tuple of (interview, created) where created is True if a new interview
            was created, or False if an existing one was updated.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        ...

    @abstractmethod
    async def get_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Retrieve the interview associated with the given offboarding process.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Interview linked to the process.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
        """
        ...

    @abstractmethod
    async def start_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Transition the process's interview from SCHEDULED to IN_PROGRESS.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The updated Interview in IN_PROGRESS state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InvalidInterviewStateTransitionError: If the interview is not in SCHEDULED state.
        """
        ...

    @abstractmethod
    async def complete_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Transition the process's interview from IN_PROGRESS to COMPLETED.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The updated Interview in COMPLETED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InvalidInterviewStateTransitionError: If the interview is not in IN_PROGRESS state.
        """
        ...

    @abstractmethod
    async def cancel_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Cancel the process's interview.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The updated Interview in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InvalidInterviewStateTransitionError: If the interview is already in a terminal state.
        """
        ...

    @abstractmethod
    async def add_interview_turns(
            self,
            process_id: OffboardingProcessId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to the in-progress interview of the given process.

        Args:
            process_id: Identifier of the offboarding process.
            turns: Ordered list of turns to append to the interview.

        Returns:
            The updated Interview with the new turns appended.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InterviewNotInProgressError: If the interview is not in IN_PROGRESS state.
            InterviewTurnOrderError: If any turn has an invalid order value.
        """
        ...


class IOffboardingDossierFacade(ABC):
    """Dossier operations scoped to an offboarding process. Used by the dossier sub-router."""

    @abstractmethod
    async def create_dossier(
            self,
            process_id: OffboardingProcessId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None,
    ) -> Dossier:
        """Create a dossier for the given offboarding process.

        Verifies the process exists, retrieves its interview, and ensures no dossier
        already exists for the process before creating.

        Args:
            process_id: Identifier of the offboarding process.
            summary: Optional free-text summary of the dossier. Defaults to None.
            sections: Optional list of dossier sections. Defaults to None.

        Returns:
            The newly created Dossier in NOT_GENERATED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            DossierAlreadyExistsForProcessError: If a dossier already exists for the process.
        """
        ...

    @abstractmethod
    async def get_dossier(self, process_id: OffboardingProcessId) -> Dossier:
        """Retrieve the dossier for the given offboarding process.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Dossier linked to the process.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            DossierNotFoundError: If no dossier exists for the given process.
        """
        ...

class IOffboardingServiceFacade(
    IOffboardingProcessFacade,
    IOffboardingInterviewFacade,
    IOffboardingDossierFacade,
    ABC
):
    """Composed facade interface for all offboarding operations.

    Inherits IOffboardingProcessFacade, IOffboardingInterviewFacade, and
    IOffboardingDossierFacade. Intended to be implemented by a single concrete
    class (OffboardingFacadeService) that satisfies all three narrow interfaces,
    while each HTTP router depends only on the narrow interface it actually uses.
    """
