"""Repository port interface for SopCandidate."""

from abc import ABC, abstractmethod

from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import ChannelId


class ISopCandidateRepository(ABC):
    """Interface for the SOP candidate repository."""

    @abstractmethod
    async def save(self, candidate: SopCandidate) -> None:
        """Persist a SOP candidate (insert or update by ID)."""

    @abstractmethod
    async def find_by_channel_and_ts(
        self, channel_id: ChannelId, message_ts: str
    ) -> SopCandidate | None:
        """Return the candidate for the given channel/message_ts, or None if not found."""

    @abstractmethod
    async def find_pending(self) -> list[SopCandidate]:
        """Return every candidate still awaiting a decision (status OFFERED)."""
