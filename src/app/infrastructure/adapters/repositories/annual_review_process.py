"""SQLModel-backed repository for annual review processes."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.application.ports.annual_review_process import IAnnualReviewProcessRepository
from app.domain.annual_review.id import AnnualReviewProcessId
from app.domain.annual_review.process import AnnualReviewProcess
from app.domain.offboarding.id import DossierId, EmployeeId, InterviewId, ManagerId
from app.infrastructure.persistence.models.annual_review_process import (
    AnnualReviewProcessModel,
)
from app.infrastructure.persistence.models.dossier import DossierModel
from app.infrastructure.persistence.models.interview import InterviewModel
from app.infrastructure.persistence.models.process import ProcessModel


class AnnualReviewProcessRepository(IAnnualReviewProcessRepository):
    """SQLModel-backed implementation of IAnnualReviewProcessRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    async def save(self, process: AnnualReviewProcess) -> None:
        """Persist an annual review process (insert or update)."""
        base = ProcessModel(
            id=process.process_id.get_id(),
            type="annual_review",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
            employee_name=process.employee_name,
            manager_name=process.manager_name,
            created_at=process.created_at,
        )
        child = AnnualReviewProcessModel(
            id=base.id,
            state=process.state.get_state().value,
        )
        await self._session.merge(base)
        await self._session.merge(child)
        await self._session.commit()

    async def find_by_id(self, process_id: AnnualReviewProcessId) -> AnnualReviewProcess | None:
        """Return the process with the given ID, or None if not found."""
        pid = process_id.get_id()
        # noinspection PyTypeChecker
        base: ProcessModel | None = await self._session.get(ProcessModel, pid)
        if not base:
            return None
        # noinspection PyTypeChecker
        child: AnnualReviewProcessModel | None = await self._session.get(
            AnnualReviewProcessModel, pid
        )
        if not child:
            return None
        return await self._to_domain(base, child)

    async def find_by_employee_id(self, employee_id: EmployeeId) -> list[AnnualReviewProcess]:
        """Return all processes for the given employee."""
        stmt = (
            select(ProcessModel, AnnualReviewProcessModel)
            .join(
                AnnualReviewProcessModel,
                col(ProcessModel.id) == col(AnnualReviewProcessModel.id),
            )
            .where(col(ProcessModel.employee_id) == employee_id.get_id())
        )
        rows = (await self._session.execute(stmt)).all()
        return [await self._to_domain(base, child) for base, child in rows]

    async def find_all(self) -> list[AnnualReviewProcess]:
        """Return all stored annual review processes."""
        stmt = select(ProcessModel, AnnualReviewProcessModel).join(
            AnnualReviewProcessModel,
            col(ProcessModel.id) == col(AnnualReviewProcessModel.id),
        )
        rows = (await self._session.execute(stmt)).all()
        return [await self._to_domain(base, child) for base, child in rows]

    async def delete(self, process_id: AnnualReviewProcessId) -> None:
        """Remove the process with the given ID (no-op if not found)."""
        base = await self._session.get(ProcessModel, process_id.get_id())
        if base:
            await self._session.delete(base)
            await self._session.commit()

    async def _to_domain(
        self, base: ProcessModel, child: AnnualReviewProcessModel
    ) -> AnnualReviewProcess:
        """Reconstruct a domain AnnualReviewProcess from its base and child persistence models."""
        interview_id, dossier_id = await self._resolve_related_ids(base.id)
        state = child.get_state_factory()
        return AnnualReviewProcess(
            process_id=AnnualReviewProcessId(base.id),
            state=state,
            employee_id=EmployeeId(base.employee_id),
            manager_id=ManagerId(base.manager_id),
            created_at=base.created_at,
            interview_id=InterviewId(interview_id) if interview_id else None,
            dossier_id=DossierId(dossier_id) if dossier_id else None,
            employee_name=base.employee_name,
            manager_name=base.manager_name,
        )

    async def _resolve_related_ids(
        self, process_id: uuid.UUID
    ) -> tuple[uuid.UUID | None, uuid.UUID | None]:
        """Resolve the interview and dossier IDs associated with this process.

        Args:
            process_id: The UUID of the process to look up.

        Returns:
            tuple[uuid.UUID | None, uuid.UUID | None]: A (interview_id, dossier_id) pair,
                each None if not yet assigned.
        """
        interview_row = (
            await self._session.execute(
                select(InterviewModel.id).where(
                    col(InterviewModel.process_id) == process_id
                )
            )
        ).scalars().first()
        dossier_row = (
            await self._session.execute(
                select(DossierModel.id).where(
                    col(DossierModel.process_id) == process_id
                )
            )
        ).scalars().first()
        return interview_row, dossier_row
