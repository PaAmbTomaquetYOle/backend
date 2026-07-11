"""Handles the inbound 'sop.creation_requested' event."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_CREATION_REQUESTED
from app.domain.sops.id import AuthorId, ChannelId


class SopCreationRequestedHandler(IInboundEventHandler):
    """Creates a SOP from a Slack-originated request.

    Expected payload: title, content, author, origin_channel, tags?
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return SOP_CREATION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Create the SOP via the SOP service, which publishes SOPCreated.

        Args:
            event: The inbound 'sop.creation_requested' event.
            context: Per-message context providing the SOP service.
        """
        payload = event.payload
        await context.sops.create_sop(
            title=payload["title"],
            content=payload["content"],
            author=AuthorId(payload["author"]),
            origin_channel=ChannelId(payload["origin_channel"]),
            tags=payload.get("tags"),
        )
