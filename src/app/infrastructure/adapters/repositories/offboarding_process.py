"""SQLModel-backed repository for offboarding processes."""

from __future__ import annotations

import uuid

from sqlmodel import Session, col, select

from app.application.ports.offboarding_process import IOffboardingProcessRepository
from app.domain.offboarding.id import (
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
    OffboardingProcessId,
)
from app.domain.offboarding.process import OffboardingProcess
from app.infrastructure.persistence.models.dossier import DossierModel
from app.infrastructure.persistence.models.interview import InterviewModel
from app.infrastructure.persistence.models.offboarding_process import (
    OffboardingProcessModel,
)
from app.infrastructure.persistence.models.process import ProcessModel


class OffboardingProcessRepository(IOffboardingProcessRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, process: OffboardingProcess) -> None:
        base = ProcessModel(
            id=process.process_id.get_id(),
            type="offboarding",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
            created_at=process.created_at,
        )
        child = OffboardingProcessModel(
            id=base.id,
            state=process.state.get_state().value,
        )
        self._session.merge(base)
        self._session.merge(child)
        self._session.commit()

    def find_by_id(self, process_id: OffboardingProcessId) -> OffboardingProcess | None:
        pid = process_id.get_id()
        base = self._session.get(ProcessModel, pid)
        if not base:
            return None
        child = self._session.get(OffboardingProcessModel, pid)
        if not child:
            return None
        return self._to_domain(base, child)

    def find_by_employee_id(self, employee_id: EmployeeId) -> list[OffboardingProcess]:
        stmt = (
            select(ProcessModel, OffboardingProcessModel)
            .join(
                OffboardingProcessModel,
                col(ProcessModel.id) == col(OffboardingProcessModel.id),
            )
            .where(col(ProcessModel.employee_id) == employee_id.get_id())
        )
        rows = self._session.exec(stmt).all()
        return [self._to_domain(base, child) for base, child in rows]

    def find_all(self) -> list[OffboardingProcess]:
        stmt = select(ProcessModel, OffboardingProcessModel).join(
            OffboardingProcessModel,
            col(ProcessModel.id) == col(OffboardingProcessModel.id),
        )
        rows = self._session.exec(stmt).all()
        return [self._to_domain(base, child) for base, child in rows]

    def delete(self, process_id: OffboardingProcessId) -> None:
        base = self._session.get(ProcessModel, process_id.get_id())
        if base:
            self._session.delete(base)
            self._session.commit()

    def _to_domain(
        self, base: ProcessModel, child: OffboardingProcessModel
    ) -> OffboardingProcess:
        interview_id, dossier_id = self._resolve_related_ids(base.id)
        state = child.get_state_factory()
        return OffboardingProcess(
            process_id=OffboardingProcessId(base.id),
            state=state,
            employee_id=EmployeeId(base.employee_id),
            manager_id=ManagerId(base.manager_id),
            created_at=base.created_at,
            interview_id=InterviewId(interview_id) if interview_id else None,
            dossier_id=DossierId(dossier_id) if dossier_id else None,
        )

    def _resolve_related_ids(
        self, process_id: uuid.UUID
    ) -> tuple[uuid.UUID | None, uuid.UUID | None]:
        interview_row = self._session.exec(
            select(InterviewModel.id).where(
                col(InterviewModel.process_id) == process_id
            )
        ).first()
        dossier_row = self._session.exec(
            select(DossierModel.id).where(
                col(DossierModel.process_id) == process_id
            )
        ).first()
        return interview_row, dossier_row
