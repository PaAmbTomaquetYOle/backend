from sqlmodel import Session, select

from app.application.ports.offboarding_process import IOffboardingProcessRepository
from app.domain.offboarding.id import EmployeeId, OffboardingProcessId
from app.domain.offboarding.process import OffboardingProcess
from app.infrastructure.persistence.models import OffboardingProcessModel


class OffboardingProcessRepository(IOffboardingProcessRepository):
    """SQLModel-backed repository for offboarding processes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, process: OffboardingProcess) -> None:
        model = OffboardingProcessModel.from_domain(process)
        self._session.merge(model)
        self._session.commit()

    def find_by_id(self, process_id: OffboardingProcessId) -> OffboardingProcess | None:
        model = self._session.get(OffboardingProcessModel, process_id.get_id())
        return model.to_domain() if model else None

    def find_by_employee_id(self, employee_id: EmployeeId) -> list[OffboardingProcess]:
        statement = select(OffboardingProcessModel).where(
            OffboardingProcessModel.employee_id == employee_id.get_id()
        )
        results = self._session.exec(statement).all()
        return [r.to_domain() for r in results]

    def find_all(self) -> list[OffboardingProcess]:
        statement = select(OffboardingProcessModel)
        results = self._session.exec(statement).all()
        return [r.to_domain() for r in results]

    def delete(self, process_id: OffboardingProcessId) -> None:
        model = self._session.get(OffboardingProcessModel, process_id.get_id())
        if model:
            self._session.delete(model)
            self._session.commit()
