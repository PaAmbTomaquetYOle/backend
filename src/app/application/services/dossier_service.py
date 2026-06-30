from datetime import UTC, datetime

from app.application.ports.dossier import IDossierRepository
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

    def __init__(self, repo: IDossierRepository) -> None:
        self._repo = repo

    async def create_dossier(
            self,
            process_id: ProcessId,
            interview_id: InterviewId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None,
    ) -> Dossier:
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
        dossier = self._repo.find_by_id(dossier_id)
        if dossier is None:
            raise DossierNotFoundError(f"Dossier {dossier_id.get_id()} not found")
        return dossier

    async def get_process_dossier(self, process_id: ProcessId) -> Dossier:
        dossier = self._repo.find_by_process_id(process_id)
        if dossier is None:
            raise DossierNotFoundError(f"No dossier found for process {process_id.get_id()}")
        return dossier
