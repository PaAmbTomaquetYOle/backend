"""Handles the inbound 'sop.candidate_offered' event (SA-16)."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_CANDIDATE_OFFERED
from app.domain.sops.id import AuthorId, ChannelId


class SopCandidateOfferedHandler(IInboundEventHandler):
    """Persists that a candidate message was offered to its author as a possible SOP.

    Expected payload: channel_id, author_id, message_ts, content.

    Persisting here (rather than only in slack-agent's in-memory cache) means
    a slack-agent restart before the author responds doesn't lose the
    candidate — slack-agent rehydrates pending candidates from this backend
    on startup.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return SOP_CANDIDATE_OFFERED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Record the offer via the SOP candidate service.

        Args:
            event: The inbound 'sop.candidate_offered' event.
            context: Per-message context providing the SOP candidate service.
        """
        payload = event.payload
        await context.sop_candidates.record_offer(
            channel_id=ChannelId(payload["channel_id"]),
            author_id=AuthorId(payload["author_id"]),
            message_ts=payload["message_ts"],
            content=payload["content"],
        )
