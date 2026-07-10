"""Inbound port (service contract) for SOP use cases."""

from abc import ABC, abstractmethod

from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop


class ISopService(ABC):
    """Use cases exposed for managing SOPs (Standard Operating Procedures)."""

    @abstractmethod
    async def create_sop(
        self,
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
    ) -> tuple[list[Sop], int]:
        """Return a page of SOPs matching the given text/tag filters plus the total count."""

    @abstractmethod
    async def update_sop(
        self,
        sop_id: SopId,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> Sop:
        """Apply a partial revision to a SOP, incrementing its version.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """

    @abstractmethod
    async def delete_sop(self, sop_id: SopId) -> None:
        """Soft-delete a SOP.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """
