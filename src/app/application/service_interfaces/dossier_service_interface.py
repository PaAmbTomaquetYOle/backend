from abc import ABC, abstractmethod

from app.domain import Dossier, DossierId, DossierSection, ProcessId


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
    async def get_process_dossier(self, process_id: ProcessId) -> Dossier:
        """
        Get a specific dossier by process id

        Args:
            process_id (ProcessId): The process id

        Returns:
            dossier (Dossier): The dossier
        """
