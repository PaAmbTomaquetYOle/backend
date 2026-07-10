"""Abstract contract for the dossier service."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.application.ports.dossier import DossierSearchResult
from app.domain import Dossier, DossierId, DossierSection, InterviewId, ProcessId
from app.domain.enums import InterviewStateEnum


class IDossierService(ABC):
    """
    Interface for dossier service
    """

    @abstractmethod
    async def create_dossier(
            self,
            process_id: ProcessId,
            interview_id: InterviewId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None
    ) -> Dossier:
        """
        Create dossier
        
        Args:
            process_id (ProcessId): The ProcessId to be associated with the dossier
            interview_id (InterviewId): The InterviewId to be associated with the dossier
            summary (str | None): The summary of the dossier
            sections (list[DossierSection]): The sections of the dossier
            
        Returns:
            dossier (Dossier): The dossier
        """

    @abstractmethod
    async def get_dossier(self, dossier_id: DossierId) -> Dossier:
        """
        Get a specific dossier

        Args:
            dossier_id (DossierId): The dossier

        Returns:
            dossier (Dossier): The dossier
        """

    @abstractmethod
    async def search_dossiers(
            self,
            employee_name: str | None = None,
            process_id: UUID | None = None,
    ) -> list[DossierSearchResult]:
        """
        Search dossiers by employee display name and/or process ID.

        Args:
            employee_name (str | None): Partial, case-insensitive employee name to match.
            process_id (UUID | None): Exact process ID to match.

        Returns:
            list[DossierSearchResult]: The matching dossiers with process display context.
        """

    @abstractmethod
    async def get_process_dossier(self, process_id: ProcessId) -> Dossier:
        """
        Get a specific dossier by process id

        Args:
            process_id (ProcessId): The process id

        Returns:
            dossier (Dossier): The dossier
        """

    @abstractmethod
    async def advance_generation(
            self,
            dossier_id: DossierId,
            interview_state: InterviewStateEnum,
    ) -> Dossier:
        """
        Drive a freshly created dossier through its generation lifecycle
        (NOT_GENERATED -> GENERATING -> DRAFT) and persist the result.

        Args:
            dossier_id (DossierId): The dossier to advance.
            interview_state (InterviewStateEnum): Current state of the associated
                interview; generation requires it to be COMPLETED.

        Returns:
            dossier (Dossier): The dossier in DRAFT state.

        Raises:
            DossierNotFoundError: If no dossier with the given ID exists.
            DossierInterviewNotCompletedError: If interview_state is not COMPLETED.
        """
