"""Concrete implementation of the SOP candidate service."""

from datetime import UTC, datetime

from app.application.ports.sop_candidate import ISopCandidateRepository
from app.application.service_interfaces.sop_candidate_service_interface import (
    ISopCandidateService,
)
from app.domain.exceptions.sops import SopCandidateNotFoundError
from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import AuthorId, ChannelId, SopCandidateId


class SopCandidateService(ISopCandidateService):
    """Orchestrates SOP candidate use cases: offer, decide, list pending.

    A focused service rather than a method bag on SopService, since a
    candidate is a distinct aggregate with its own lifecycle (offered ->
    accepted | rejected) — the actual SOP is still created by SopService via
    the existing 'sop.creation_requested' flow.
    """

    def __init__(self, repo: ISopCandidateRepository) -> None:
        """Set up the service with a repository.

        Args:
            repo: The repository used to persist and retrieve candidates.
        """
        self._repo = repo

    async def record_offer(
        self,
        channel_id: ChannelId,
        author_id: AuthorId,
        message_ts: str,
        content: str,
    ) -> SopCandidate:
        """Persist a newly offered candidate, or return the existing one if redelivered."""
        existing = await self._repo.find_by_channel_and_ts(channel_id, message_ts)
        if existing is not None:
            return existing

        candidate = SopCandidate(
            candidate_id=SopCandidateId(),
            channel_id=channel_id,
            author_id=author_id,
            message_ts=message_ts,
            content=content,
            created_at=datetime.now(UTC),
        )
        await self._repo.save(candidate)
        return candidate

    async def record_decision(
        self,
        channel_id: ChannelId,
        message_ts: str,
        accepted: bool,
    ) -> SopCandidate:
        """Apply the author's decision to a previously offered candidate and persist it."""
        candidate = await self._repo.find_by_channel_and_ts(channel_id, message_ts)
        if candidate is None:
            raise SopCandidateNotFoundError(channel_id.get_id(), message_ts)

        if accepted:
            candidate.mark_accepted()
        else:
            candidate.mark_rejected()
        await self._repo.save(candidate)
        return candidate

    async def list_pending(self) -> list[SopCandidate]:
        """Return every candidate still awaiting a decision."""
        return await self._repo.find_pending()
