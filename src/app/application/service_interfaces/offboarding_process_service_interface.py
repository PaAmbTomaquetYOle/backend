from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.application.service_interfaces.process_service_interface import IProcessService
from app.domain import (
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
    OffboardingProcess,
    OffboardingProcessId,
    OffboardingProcessStateEnum,
)


class IOffboardingProcessService(IProcessService, ABC):
    @abstractmethod
    async def create_process(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId
    ) -> OffboardingProcess:
        ...

    @abstractmethod
    async def get_process(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def get_filtered_processes(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            interview_id: InterviewId | None = None,
            dossier_id: DossierId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> Iterable[OffboardingProcess]:
        ...

    @abstractmethod
    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def submit_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def complete_offboarding(
            self,
            process_id: OffboardingProcessId
    ) -> OffboardingProcess:
        ...

    @abstractmethod
    async def delete_process(self, process_id: OffboardingProcessId) -> None: ...
