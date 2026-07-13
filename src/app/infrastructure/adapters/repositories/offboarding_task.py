"""SQLModel-backed repository for offboarding tasks."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.application.ports.offboarding_task import IOffboardingTaskRepository
from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask
from app.infrastructure.persistence.models.offboarding_task import OffboardingTaskModel


class OffboardingTaskRepository(IOffboardingTaskRepository):
    """SQLModel-backed implementation of IOffboardingTaskRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    async def replace_for_process(
        self, process_id: OffboardingProcessId, tasks: list[OffboardingTask]
    ) -> None:
        """Delete every task stored for the process and insert the given full set."""
        stmt = select(OffboardingTaskModel).where(
            col(OffboardingTaskModel.process_id) == process_id.get_id()
        )
        existing = (await self._session.execute(stmt)).scalars().all()
        for row in existing:
            await self._session.delete(row)
        await self._session.flush()

        for task in tasks:
            self._session.add(OffboardingTaskModel.from_domain(task))

        await self._session.commit()

    async def find_by_process_id(
        self, process_id: OffboardingProcessId
    ) -> list[OffboardingTask]:
        """Return every task stored for the given process."""
        stmt = select(OffboardingTaskModel).where(
            col(OffboardingTaskModel.process_id) == process_id.get_id()
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [row.to_domain() for row in rows]
