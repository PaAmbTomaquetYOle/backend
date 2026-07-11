"""Inbound port (service contract) for SOP candidate use cases."""

from abc import ABC, abstractmethod

from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import AuthorId, ChannelId


class ISopCandidateService(ABC):
    """Use cases for tracking SOP candidates awaiting an author decision (SA-16)."""

    @abstractmethod
    async def record_offer(
        self,
        channel_id: ChannelId,
        author_id: AuthorId,
        message_ts: str,
        content: str,
    ) -> SopCandidate:
        """Persist that a candidate message was offered to its author as a possible SOP.

        Idempotent: redelivering the same channel/message_ts returns the
        existing candidate instead of creating a duplicate.
        """

    @abstractmethod
    async def record_decision(
        self,
        channel_id: ChannelId,
        message_ts: str,
        accepted: bool,
    ) -> SopCandidate:
        """Record the author's accept/reject decision for a previously offered candidate.

        Raises:
            SopCandidateNotFoundError: If no candidate exists for the channel/message_ts.
            InvalidSopCandidateTransitionError: If a decision was already recorded.
        """

    @abstractmethod
    async def list_pending(self) -> list[SopCandidate]:
        """Return every candidate still awaiting a decision, for rehydration."""
