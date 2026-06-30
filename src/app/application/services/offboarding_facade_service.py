from datetime import datetime

from app.application.service_interfaces.dossier_service_interface import IDossierService
from app.application.service_interfaces.interview_service_interface import IInterviewService
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.service_interfaces.offboarding_process_service_interface import (
    IOffboardingProcessService,
)
from app.domain import (
    Dossier,
    DossierSection,
    EmployeeId,
    Interview,
    InterviewTurn,
    ManagerId,
    OffboardingProcess,
    OffboardingProcessId,
)
from app.domain.enums import OffboardingProcessStateEnum
from app.domain.exceptions.dossier import DossierAlreadyExistsForProcessError


class OffboardingFacadeService(IOffboardingServiceFacade):

    def __init__(
            self,
            process_service: IOffboardingProcessService,
            interview_service: IInterviewService,
            dossier_service: IDossierService,
    ) -> None:
        self._process_service = process_service
        self._interview_service = interview_service
        self._dossier_service = dossier_service

    async def create_offboarding(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
    ) -> OffboardingProcess:
        return await self._process_service.create_process(employee_id, manager_id)

    async def get_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        return await self._process_service.get_process(process_id)

    async def list_offboardings(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> list[OffboardingProcess]:
        results = await self._process_service.get_filtered_processes(
            employee_id=employee_id,
            manager_id=manager_id,
            state=state,
        )
        return list(results)

    async def delete_offboarding(self, process_id: OffboardingProcessId) -> None:
        await self._process_service.delete_process(process_id)

    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        return await self._process_service.start_offboarding(process_id)

    async def submit_offboarding_for_review(
            self,
            process_id: OffboardingProcessId
    ) -> OffboardingProcess:
        return await self._process_service.submit_for_review(process_id)

    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        return await self._process_service.complete_offboarding(process_id)

    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        return await self._process_service.cancel_offboarding(process_id)

    async def upsert_interview(
            self,
            process_id: OffboardingProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        await self._process_service.get_process(process_id)
        return await self._interview_service.upsert_interview(process_id, scheduled_at, turns)

    async def get_interview(self, process_id: OffboardingProcessId) -> Interview:
        await self._process_service.get_process(process_id)
        return await self._interview_service.get_process_interview(process_id)

    async def start_interview(self, process_id: OffboardingProcessId) -> Interview:
        interview = await self.get_interview(process_id)
        return await self._interview_service.start_interview(interview.interview_id)

    async def complete_interview(self, process_id: OffboardingProcessId) -> Interview:
        interview = await self.get_interview(process_id)
        return await self._interview_service.complete_interview(interview.interview_id)

    async def cancel_interview(self, process_id: OffboardingProcessId) -> Interview:
        interview = await self.get_interview(process_id)
        return await self._interview_service.cancel_interview(interview.interview_id)

    async def add_interview_turns(
            self,
            process_id: OffboardingProcessId,
            turns: list[InterviewTurn],
    ) -> Interview:
        interview = await self.get_interview(process_id)
        return await self._interview_service.add_turns(interview.interview_id, turns)

    async def create_dossier(
            self,
            process_id: OffboardingProcessId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None,
    ) -> Dossier:
        await self._process_service.get_process(process_id)
        interview = await self._interview_service.get_process_interview(process_id)
        existing = None
        try:
            existing = await self._dossier_service.get_process_dossier(process_id)
        except Exception:
            pass
        if existing is not None:
            raise DossierAlreadyExistsForProcessError(str(process_id.get_id()))
        return await self._dossier_service.create_dossier(
            process_id=process_id,
            interview_id=interview.interview_id,
            summary=summary,
            sections=sections,
        )

    async def get_dossier(self, process_id: OffboardingProcessId) -> Dossier:
        await self._process_service.get_process(process_id)
        return await self._dossier_service.get_process_dossier(process_id)
