from abc import ABC, abstractmethod

from app.domain import Dossier, DossierSection, ProcessId


class IDossierService(ABC):
    """
    Interface for dossier service
    """

    @abstractmethod
    async def create_dossier(
            self,
            process_id: ProcessId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None
    ) -> Dossier:
        """
        Create dossier
        
        Args:
            process_id (ProcessId): The ProcessId to be associated with the dossier
            summary (str | None): The summary of the dossier
            sections (list[DossierSection]): The sections of the dossier
            
        Returns:
            dossier (Dossier): The dossier
        """