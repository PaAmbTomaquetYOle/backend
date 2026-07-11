"""SQLModel-backed repository for SOP candidates."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.application.ports.sop_candidate import ISopCandidateRepository
from app.domain.enums import SopCandidateStatus
from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import ChannelId
from app.infrastructure.persistence.models.sop_candidate import SopCandidateModel


class SopCandidateRepository(ISopCandidateRepository):
    """SQLModel-backed implementation of ISopCandidateRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    async def save(self, candidate: SopCandidate) -> None:
        """Persist a SOP candidate (insert or update by ID)."""
        model = SopCandidateModel.from_domain(candidate)
        await self._session.merge(model)
        await self._session.commit()

    async def find_by_channel_and_ts(
        self, channel_id: ChannelId, message_ts: str
    ) -> SopCandidate | None:
        """Return the candidate for the given channel/message_ts, or None if not found."""
        stmt = select(SopCandidateModel).where(
            col(SopCandidateModel.channel_id) == channel_id.get_id(),
            col(SopCandidateModel.message_ts) == message_ts,
        )
        model = (await self._session.execute(stmt)).scalars().first()
        return model.to_domain() if model is not None else None

    async def find_pending(self) -> list[SopCandidate]:
        """Return every candidate still awaiting a decision (status OFFERED)."""
        stmt = select(SopCandidateModel).where(
            col(SopCandidateModel.status) == SopCandidateStatus.OFFERED.value
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [model.to_domain() for model in rows]
