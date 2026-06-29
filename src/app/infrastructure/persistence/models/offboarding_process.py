"""SQLModel persistence models for the offboarding domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.offboarding.id import EmployeeId, ManagerId, OffboardingProcessId
from app.domain.offboarding.process import OffboardingProcess
from app.domain.offboarding.state.base import OffboardingProcessState
from app.domain.offboarding.state.finished import FinishedState
from app.domain.offboarding.state.in_progress import InProgressState
from app.domain.offboarding.state.not_started import NotStartedState
from app.domain.offboarding.state.pending_revision import PendingRevisionState

_STATE_FACTORIES: dict[str, type[OffboardingProcessState]] = {
    OffboardingProcessStateEnum.NOT_STARTED.value: NotStartedState,
    OffboardingProcessStateEnum.IN_PROGRESS.value: InProgressState,
    OffboardingProcessStateEnum.PENDING_REVISION.value: PendingRevisionState,
    OffboardingProcessStateEnum.FINISHED.value: FinishedState,
}


class OffboardingProcessModel(SQLModel, table=True):
    __tablename__ = "offboarding_processes"

    id: uuid.UUID = Field(primary_key=True)
    employee_id: uuid.UUID = Field(index=True)
    manager_id: uuid.UUID
    state: str
    created_at: datetime

    @classmethod
    def from_domain(cls, process: OffboardingProcess) -> OffboardingProcessModel:
        return cls(
            id=process.process_id.get_id(),
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
            state=process.state.get_state().value,
            created_at=process.created_at,
        )

    def to_domain(self) -> OffboardingProcess:
        state = _STATE_FACTORIES[self.state]()
        return OffboardingProcess(
            process_id=OffboardingProcessId(self.id),
            state=state,
            employee_id=EmployeeId(self.employee_id),
            manager_id=ManagerId(self.manager_id),
            created_at=self.created_at,
        )
