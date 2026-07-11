"""Repository port interface for Sop."""

from abc import ABC, abstractmethod

from app.application.read_models.sop_search_hit import SopSearchHit
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
    ) -> tuple[list[SopSearchHit], int]:
        """Search non-deleted SOPs, filtering by full-text query and/or tags.

        Args:
            text: Free-text search query matched against SOP title and content
                via Postgres full-text search, ranked by relevance
                (``ts_rank``) when present. None to skip text filtering.
            tags: Tags a SOP must ALL have (match-all). None/empty to skip.
            page: 1-indexed page number.
            size: Number of items per page.

        Returns:
            tuple[list[SopSearchHit], int]: The page of matching SOPs (each
                with an optional highlighted snippet) and the total count of
                matches across all pages.
        """
