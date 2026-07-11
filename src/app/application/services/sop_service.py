"""Concrete implementation of the SOP service."""

import logging
from datetime import UTC, datetime

from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.sop import ISopRepository
from app.application.read_models.sop_search_hit import SopSearchHit
from app.application.service_interfaces.sop_service_interface import ISopService
from app.domain.events.sop_events import SOPCreated, SOPDeleted, SOPUpdated
from app.domain.exceptions.sops import SopNotFoundError
from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop

logger = logging.getLogger(__name__)


class SopService(ISopService):
    """Orchestrates SOP use cases: create, read, search, update, soft-delete.

    Delegates persistence to ISopRepository and publishes SOPCreated on
    creation via a defensive helper, mirroring OffboardingFacadeService.
    """

    def __init__(
        self,
        repo: ISopRepository,
        event_publisher: IEventPublisher | None = None,
    ) -> None:
        """Set up the service with a repository and an optional event publisher.

        Args:
            repo: The repository used to persist and retrieve SOPs.
            event_publisher: Optional publisher for domain events. If None,
                events are not published.
        """
        self._repo = repo
        self._event_publisher = event_publisher

    async def _publish(self, event) -> None:
        """Publish a domain event, logging a warning if publishing fails.

        Args:
            event: The domain event to publish.
        """
        if self._event_publisher is not None:
            try:
                await self._event_publisher.publish(event)
            except Exception:
                logger.warning("Failed to publish event %s", event.event_type, exc_info=True)

    async def create_sop(
        self,
        title: str,
        content: str,
        author: AuthorId,
        origin_channel: ChannelId,
        tags: list[str] | None = None,
    ) -> Sop:
        """Create and persist a new SOP, then publish SOPCreated.

        Args:
            title: Short human-authored title, used for search and display.
            content: The operational knowledge text.
            author: Identifier of the Slack user who authored the SOP.
            origin_channel: Identifier of the Slack channel the SOP originated from.
            tags: Free-form categorization tags. Defaults to none.

        Returns:
            The newly created and persisted Sop.
        """
        sop = Sop(
            sop_id=SopId(),
            title=title,
            content=content,
            author=author,
            tags=tags or [],
            origin_channel=origin_channel,
            created_at=datetime.now(UTC),
        )
        await self._repo.save(sop)
        await self._publish(SOPCreated(
            sop_id=sop.sop_id.get_id(),
            title=sop.title,
            author=sop.author.get_id(),
            origin_channel=sop.origin_channel.get_id(),
            tags=sop.tags,
            version=sop.version,
            created_at=sop.created_at,
        ))
        return sop

    async def get_sop(self, sop_id: SopId) -> Sop:
        """Retrieve a SOP by ID.

        Args:
            sop_id: Identifier of the SOP to retrieve.

        Returns:
            The matching Sop.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """
        sop = await self._repo.find_by_id(sop_id)
        if sop is None:
            raise SopNotFoundError(str(sop_id.get_id()))
        return sop

    async def search_sops(
        self,
        text: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[SopSearchHit], int]:
        """Return a page of SOPs matching the given text/tag filters plus the total count.

        Args:
            text: Free-text search query. Defaults to None (no text filter).
            tags: Tags a SOP must ALL have. Defaults to None (no tag filter).
            page: 1-indexed page number. Defaults to 1.
            size: Number of items per page. Defaults to 20.

        Returns:
            A (items, total) tuple.
        """
        return await self._repo.search(text=text, tags=tags, page=page, size=size)

    async def update_sop(
        self,
        sop_id: SopId,
        editor: AuthorId,
        origin_channel: ChannelId,
        content: str | None = None,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> Sop:
        """Apply a partial revision to a SOP, persist it, and publish SOPUpdated.

        Args:
            sop_id: Identifier of the SOP to revise.
            editor: Identifier of the Slack user requesting the revision.
            origin_channel: Identifier of the Slack channel the request came from.
            content: New content, if being changed. Defaults to None (unchanged).
            tags: New tag list, if being changed. Defaults to None (unchanged).
            title: New title, if being changed. Defaults to None (unchanged).

        Returns:
            The updated Sop with its version incremented.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """
        sop = await self.get_sop(sop_id)
        sop.revise(content=content, tags=tags, title=title)
        await self._repo.save(sop)
        await self._publish(SOPUpdated(
            sop_id=sop.sop_id.get_id(),
            title=sop.title,
            editor=editor.get_id(),
            origin_channel=origin_channel.get_id(),
            tags=sop.tags,
            version=sop.version,
            updated_at=sop.updated_at,
        ))
        return sop

    async def delete_sop(
        self,
        sop_id: SopId,
        requester: AuthorId,
        origin_channel: ChannelId,
    ) -> None:
        """Soft-delete a SOP and publish SOPDeleted.

        Args:
            sop_id: Identifier of the SOP to delete.
            requester: Identifier of the Slack user requesting the deletion.
            origin_channel: Identifier of the Slack channel the request came from.

        Raises:
            SopNotFoundError: If no non-deleted SOP with the given ID exists.
        """
        sop = await self.get_sop(sop_id)
        sop.mark_deleted()
        await self._repo.save(sop)
        await self._publish(SOPDeleted(
            sop_id=sop.sop_id.get_id(),
            requester=requester.get_id(),
            origin_channel=origin_channel.get_id(),
            deleted_at=sop.deleted_at,
        ))
