from abc import ABC, abstractmethod
from datetime import datetime

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


class IOffboardingProcessFacade(ABC):
    """Process CRUD and lifecycle transitions. Used by the offboarding router."""

    @abstractmethod
    async def create_offboarding(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
    ) -> OffboardingProcess: ...

    @abstractmethod
    async def get_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def list_offboardings(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> list[OffboardingProcess]: ...

    @abstractmethod
    async def delete_offboarding(self, process_id: OffboardingProcessId) -> None: ...

    @abstractmethod
    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def submit_offboarding_for_review(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...

    @abstractmethod
    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess: ...


class IOffboardingInterviewFacade(ABC):
    """Interview operations scoped to an offboarding process. Used by the interview sub-router."""

    @abstractmethod
    async def upsert_interview(
            self,
            process_id: OffboardingProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]: ...

    @abstractmethod
    async def get_interview(self, process_id: OffboardingProcessId) -> Interview: ...

    @abstractmethod
    async def start_interview(self, process_id: OffboardingProcessId) -> Interview: ...

    @abstractmethod
    async def complete_interview(self, process_id: OffboardingProcessId) -> Interview: ...

    @abstractmethod
    async def cancel_interview(self, process_id: OffboardingProcessId) -> Interview: ...

    @abstractmethod
    async def add_interview_turns(
            self,
            process_id: OffboardingProcessId,
            turns: list[InterviewTurn],
    ) -> Interview: ...


class IOffboardingDossierFacade(ABC):
    """Dossier operations scoped to an offboarding process. Used by the dossier sub-router."""

    @abstractmethod
    async def create_dossier(
            self,
            process_id: OffboardingProcessId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None,
    ) -> Dossier: ...

    @abstractmethod
    async def get_dossier(self, process_id: OffboardingProcessId) -> Dossier: ...

class IOffboardingServiceFacade(
    IOffboardingProcessFacade,
    IOffboardingInterviewFacade,
    IOffboardingDossierFacade,
    ABC
):
    """Facade interface for offboarding process, interview, and dossier operations."""