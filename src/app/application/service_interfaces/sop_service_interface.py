"""Inbound port (service contract) for SOP use cases."""

from abc import ABC, abstractmethod

from app.application.read_models.sop_search_hit import SopSearchHit
from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop


class ISopService(ABC):
    """Use cases exposed for managing SOPs (Standard Operating Procedures)."""

    @abstractmethod
    async def create_sop(
        self,
        title: str,
        content: str,
        author: AuthorId,
        origin_channel: ChannelId,
        tags: list[str] | None = None,
    ) -> Sop:
        """Create and persist a new SOP, publishing SOPCreated."""

    @abstractmethod
    async def get_sop(self, sop_id: SopId) -> Sop:
        """Retrieve a SOP by ID.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """

    @abstractmethod
    async def search_sops(
        self,
        text: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[SopSearchHit], int]:
        """Return a page of SOPs matching the given text/tag filters plus the total count."""

    @abstractmethod
    async def update_sop(
        self,
        sop_id: SopId,
        editor: AuthorId,
        origin_channel: ChannelId,
        content: str | None = None,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> Sop:
        """Apply a partial revision to a SOP, incrementing its version and publishing SOPUpdated.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """

    @abstractmethod
    async def delete_sop(
        self,
        sop_id: SopId,
        requester: AuthorId,
        origin_channel: ChannelId,
    ) -> None:
        """Soft-delete a SOP and publish SOPDeleted.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """
