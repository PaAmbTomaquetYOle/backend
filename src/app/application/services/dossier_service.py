"""Concrete implementation of the dossier service."""

from datetime import UTC, datetime
from uuid import UUID

from app.application.ports.dossier import DossierSearchResult, IDossierRepository
from app.application.service_interfaces.dossier_service_interface import IDossierService
from app.domain import (
    Dossier,
    DossierId,
    DossierSection,
    InterviewId,
    NotGeneratedDossierState,
    ProcessId,
)
from app.domain.exceptions.dossier import DossierNotFoundError


class DossierService(IDossierService):
    """Orchestrates dossier lifecycle operations. Delegates persistence to IDossierRepository."""

    def __init__(self, repo: IDossierRepository) -> None:
        """Set up the service with a repository.

        Args:
            repo: The repository used to persist and retrieve dossiers.
        """
        self._repo = repo

    async def create_dossier(
            self,
            process_id: ProcessId,
            interview_id: InterviewId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None,
    ) -> Dossier:
        """Create and persist a new dossier in NOT_GENERATED state.

        Args:
            process_id: Identifier of the offboarding process this dossier belongs to.
            interview_id: Identifier of the interview that informs this dossier.
            summary: Optional free-text summary. Defaults to None.
            sections: Optional list of dossier sections. Defaults to None.

        Returns:
            The newly created and persisted Dossier.
        """
        dossier = Dossier(
            dossier_id=DossierId(),
            process_id=process_id,
            interview_id=interview_id,
            state=NotGeneratedDossierState(),
            created_at=datetime.now(UTC),
            summary=summary,
            sections=sections,
        )
        self._repo.save(dossier)
        return dossier

    async def get_dossier(self, dossier_id: DossierId) -> Dossier:
        """Retrieve a dossier by its own ID.

        Args:
            dossier_id: Identifier of the dossier to retrieve.

        Returns:
            The matching Dossier.

        Raises:
            DossierNotFoundError: If no dossier with the given ID exists.
        """
        dossier = self._repo.find_by_id(dossier_id)
        if dossier is None:
            raise DossierNotFoundError(f"Dossier {dossier_id.get_id()} not found")
        return dossier

    async def search_dossiers(
            self,
            employee_name: str | None = None,
            process_id: UUID | None = None,
    ) -> list[DossierSearchResult]:
        """Search dossiers by employee display name and/or process ID.

        Args:
            employee_name: Partial, case-insensitive employee name to match. Defaults to None.
            process_id: Exact process ID to match. Defaults to None.

        Returns:
            The matching dossiers with process display context.
        """
        return self._repo.search(employee_name=employee_name, process_id=process_id)

    async def get_process_dossier(self, process_id: ProcessId) -> Dossier:
        """Retrieve the dossier associated with the given offboarding process.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Dossier linked to the process.

        Raises:
            DossierNotFoundError: If no dossier exists for the given process.
        """
        dossier = self._repo.find_by_process_id(process_id)
        if dossier is None:
            raise DossierNotFoundError(f"No dossier found for process {process_id.get_id()}")
        return dossier
