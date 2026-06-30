from datetime import UTC, datetime

from app.application.ports.offboarding_process import IOffboardingProcessRepository
from app.application.service_interfaces.offboarding_process_service_interface import (
    IOffboardingProcessService,
)
from app.domain import (
    EmployeeId,
    ManagerId,
    NotStartedState,
    OffboardingProcess,
    OffboardingProcessId,
    ProcessId,
)
from app.domain.enums import OffboardingProcessStateEnum
from app.domain.exceptions.offboarding import ProcessNotFoundError


class OffboardingProcessService(IOffboardingProcessService):

    def __init__(self, repo: IOffboardingProcessRepository) -> None:
        self._repo = repo

    async def create_process(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
    ) -> OffboardingProcess:
        process = OffboardingProcess(
            process_id=OffboardingProcessId(),
            state=NotStartedState(),
            employee_id=employee_id,
            manager_id=manager_id,
            created_at=datetime.now(UTC),
        )
        self._repo.save(process)
        return process

    async def get_process(self, process_id: ProcessId) -> OffboardingProcess:
        process = self._repo.find_by_id(OffboardingProcessId(process_id.get_id()))
        if process is None:
            raise ProcessNotFoundError(str(process_id.get_id()))
        return process

    async def get_filtered_processes(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            **_kwargs,
    ) -> list[OffboardingProcess]:
        if employee_id is not None:
            processes = self._repo.find_by_employee_id(employee_id)
        else:
            processes = self._repo.find_all()
        if manager_id is not None:
            processes = [p for p in processes if p.manager_id.get_id() == manager_id.get_id()]
        return processes

    async def get_filtered_processes_by_state(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> list[OffboardingProcess]:
        processes = await self.get_filtered_processes(employee_id=employee_id, manager_id=manager_id)
        if state is not None:
            processes = [p for p in processes if p.state_value == state]
        return processes

    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        process = await self.get_process(process_id)
        process.start()
        self._repo.save(process)
        return process

    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        process = await self.get_process(process_id)
        process.cancel()
        self._repo.save(process)
        return process

    async def submit_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        process = await self.get_process(process_id)
        process.submit_for_review()
        self._repo.save(process)
        return process

    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        process = await self.get_process(process_id)
        process.complete()
        self._repo.save(process)
        return process

    async def delete_process(self, process_id: OffboardingProcessId) -> None:
        await self.get_process(process_id)
        self._repo.delete(process_id)
