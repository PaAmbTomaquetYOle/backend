"""SQLModel-backed repository for interviews."""
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.application.ports.interview import IInterviewRepository
from app.domain.interview.interview import Interview
from app.domain.offboarding.id import InterviewId, OffboardingProcessId
from app.infrastructure.persistence.models.interview import (
    InterviewModel,
    InterviewTurnModel,
)


class InterviewRepository(IInterviewRepository):
    """SQLModel-backed implementation of IInterviewRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    async def save(self, interview: Interview) -> None:
        """Persist an interview and all its turns (insert or update)."""
        model = InterviewModel.from_domain(interview)
        await self._session.merge(model)
        await self._session.flush()

        stmt = select(InterviewTurnModel).where(
            col(InterviewTurnModel.interview_id) == model.id
        )
        existing_turns = (await self._session.execute(stmt)).scalars().all()
        for turn in existing_turns:
            await self._session.delete(turn)
        await self._session.flush()

        interview_id = model.id
        for turn in interview.turns:
            turn_model = InterviewTurnModel.from_domain(turn, interview_id)
            self._session.add(turn_model)

        await self._session.commit()

    async def find_by_id(self, interview_id: InterviewId) -> Interview | None:
        """Return the interview with the given ID, or None if not found."""
        model = await self._session.get(InterviewModel, interview_id.get_id())
        if not model:
            return None
        turns: Sequence[InterviewTurnModel] = (
            await self._session.execute(
                select(InterviewTurnModel).where(
                    col(InterviewTurnModel.interview_id) == model.id
                )
            )
        ).scalars().all()
        # noinspection PyTypeChecker
        return model.to_domain(list(turns))

    async def find_by_process_id(self, process_id: OffboardingProcessId) -> Interview | None:
        """Return the interview for the given process, or None if not found."""
        model: InterviewModel | None = (
            await self._session.execute(
                select(InterviewModel).where(
                    col(InterviewModel.process_id) == process_id.get_id()
                )
            )
        ).scalars().first()
        if not model:
            return None
        turns: Sequence[InterviewTurnModel] = (
            await self._session.execute(
                select(InterviewTurnModel).where(
                    col(InterviewTurnModel.interview_id) == model.id
                )
            )
        ).scalars().all()
        return model.to_domain(list(turns))

    async def find_all(self) -> list[Interview]:
        """Return all stored interviews."""
        models = (await self._session.execute(select(InterviewModel))).scalars().all()
        result: list[Interview] = []
        for model in models:
            turns = (
                await self._session.execute(
                    select(InterviewTurnModel).where(
                        col(InterviewTurnModel.interview_id) == model.id
                    )
                )
            ).scalars().all()
            result.append(model.to_domain(list(turns)))
        return result

    async def delete(self, interview_id: InterviewId) -> None:
        """Remove the interview with the given ID (no-op if not found)."""
        model = await self._session.get(InterviewModel, interview_id.get_id())
        if model:
            await self._session.delete(model)
            await self._session.commit()
