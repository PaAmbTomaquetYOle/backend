from abc import ABC, abstractmethod

from app.application.service_interfaces.process_service_interface import IProcessService
from app.domain import OffboardingProcess, OffboardingProcessId


class IOffboardingProcessService(IProcessService, ABC):

    @abstractmethod
    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def submit_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def delete_process(self, process_id: OffboardingProcessId) -> None: ...
