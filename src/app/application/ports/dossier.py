"""Repository port interface for Dossier."""

from abc import ABC, abstractmethod

from app.domain.dossier.dossier import Dossier
from app.domain.offboarding.id import DossierId, InterviewId, OffboardingProcessId


class IDossierRepository(ABC):
    """Interface for the Dossier repository."""

    @abstractmethod
    def save(self, dossier: Dossier) -> None:
        """Persist a dossier (insert or update by ID)."""

    @abstractmethod
    def find_by_id(self, dossier_id: DossierId) -> Dossier | None:
        """Return the dossier with the given ID, or None if not found."""

    @abstractmethod
    def find_by_process_id(self, process_id: OffboardingProcessId) -> Dossier | None:
        """Return the dossier for the given process, or None if not found."""

    @abstractmethod
    def find_by_interview_id(self, interview_id: InterviewId) -> Dossier | None:
        """Return the dossier associated with the given interview, or None if not found."""

    @abstractmethod
    def find_all(self) -> list[Dossier]:
        """Return all stored dossiers."""

    @abstractmethod
    def delete(self, dossier_id: DossierId) -> None:
        """Remove the dossier with the given ID (no-op if not found)."""
