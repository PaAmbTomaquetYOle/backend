from abc import ABC, abstractmethod

from app.application.service_interfaces.process_service_interface import IProcessService
from app.domain import OffboardingProcessId


class IOffboardingProcessService(IProcessService, ABC):
    """
    Interface for the offboarding process service.
    """
    @abstractmethod
    async def start_offboarding(self, process_id: OffboardingProcessId) -> None:
        """
        Starts the offboarding process.

        Args:
            process_id (OffboardingProcessId): The offboarding process id.
        """

    @abstractmethod
    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> None:
        """
        Cancels the offboarding process.

        Args:
            process_id (OffboardingProcessId): The offboarding process id.
        """