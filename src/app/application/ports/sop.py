"""Repository port interface for Sop."""

from abc import ABC, abstractmethod

from app.domain.sops.id import SopId
from app.domain.sops.sop import Sop


class ISopRepository(ABC):
    """Interface for the SOP repository."""

    @abstractmethod
    async def save(self, sop: Sop) -> None:
        """Persist a SOP (insert or update by ID), including its tags."""

    @abstractmethod
    async def find_by_id(self, sop_id: SopId) -> Sop | None:
        """Return the non-deleted SOP with the given ID, or None if not found."""

    @abstractmethod
    async def search(
        self,
        text: str | None,
        tags: list[str] | None,
        page: int,
        size: int,
    ) -> tuple[list[Sop], int]:
        """Search non-deleted SOPs, filtering by full-text query and/or tags.

        Args:
            text: Free-text search query matched against SOP content via
                Postgres full-text search. None to skip text filtering.
            tags: Tags a SOP must ALL have (match-all). None/empty to skip.
            page: 1-indexed page number.
            size: Number of items per page.

        Returns:
            tuple[list[Sop], int]: The page of matching SOPs and the total
                count of matches across all pages.
        """

    @abstractmethod
    async def soft_delete(self, sop_id: SopId) -> None:
        """Mark the SOP with the given ID as deleted (no-op if not found)."""
