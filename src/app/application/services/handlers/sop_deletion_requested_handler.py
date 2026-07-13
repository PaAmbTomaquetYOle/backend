"""Handles the inbound 'sop.deletion_requested' event (BE-21)."""

import logging
from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_DELETION_REQUESTED
from app.domain.exceptions.sops import SopNotFoundError
from app.domain.sops.id import AuthorId, ChannelId, SopId

logger = logging.getLogger(__name__)


class SopDeletionRequestedHandler(IInboundEventHandler):
    """Soft-deletes a SOP.

    Expected payload: sop_id, requester, origin_channel

    A request targeting a SOP that no longer exists (e.g. already deleted
    by a redelivered message) is logged and dropped rather than sent to the
    DLQ, since Kafka's at-least-once, cross-topic delivery makes this an
    expected race, not message corruption.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return SOP_DELETION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Soft-delete the SOP via the SOP service, which publishes SOPDeleted.

        Args:
            event: The inbound 'sop.deletion_requested' event.
            context: Per-message context providing the SOP service.
        """
        payload = event.payload
        sop_id = payload["sop_id"]
        try:
            await context.sops.delete_sop(
                SopId(UUID(sop_id)),
                requester=AuthorId(payload["requester"]),
                origin_channel=ChannelId(payload["origin_channel"]),
            )
        except SopNotFoundError:
            logger.warning(
                "sop.deletion_requested for unknown SOP %s; dropping", sop_id
            )
