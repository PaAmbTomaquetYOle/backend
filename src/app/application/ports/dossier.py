"""Repository port interface for Dossier."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.dossier.dossier import Dossier
from app.domain.offboarding.id import DossierId, InterviewId, ProcessId


class DossierSearchResult:
    """A dossier paired with the display context of the process it belongs to."""

    def __init__(
        self,
        dossier: Dossier,
        employee_id: str,
        manager_id: str,
        employee_name: str | None,
        manager_name: str | None,
    ) -> None:
        self.dossier = dossier
        self.employee_id = employee_id
        self.manager_id = manager_id
        self.employee_name = employee_name
        self.manager_name = manager_name


class IDossierRepository(ABC):
    """Interface for the Dossier repository."""

    @abstractmethod
    async def save(self, dossier: Dossier) -> None:
        """Persist a dossier (insert or update by ID)."""

    @abstractmethod
    async def find_by_id(self, dossier_id: DossierId) -> Dossier | None:
        """Return the dossier with the given ID, or None if not found."""

    @abstractmethod
    async def find_by_process_id(self, process_id: ProcessId) -> Dossier | None:
        """Return the dossier for the given process, or None if not found."""

    @abstractmethod
    async def find_by_interview_id(self, interview_id: InterviewId) -> Dossier | None:
        """Return the dossier associated with the given interview, or None if not found."""

    @abstractmethod
    async def find_all(self) -> list[Dossier]:
        """Return all stored dossiers."""

    @abstractmethod
    async def search(
        self,
        employee_name: str | None = None,
        process_id: UUID | None = None,
    ) -> list[DossierSearchResult]:
        """Search dossiers by employee display name (case-insensitive, partial match)
        and/or by their associated process ID.

        At least one of the two filters is expected to be provided by the caller.
        """

    @abstractmethod
    async def delete(self, dossier_id: DossierId) -> None:
        """Remove the dossier with the given ID (no-op if not found)."""
