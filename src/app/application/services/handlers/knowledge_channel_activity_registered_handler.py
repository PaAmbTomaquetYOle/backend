"""Handles the inbound 'knowledge_graph.channel_activity_registered' event."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED


class KnowledgeChannelActivityRegisteredHandler(IInboundEventHandler):
    """Registers that a person is active in a channel in the knowledge graph.

    Expected payload: person_id, person_name, channel_id, channel_name
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return KNOWLEDGE_CHANNEL_ACTIVITY_REGISTERED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Register the channel activity via the knowledge graph service.

        Args:
            event: The inbound 'knowledge_graph.channel_activity_registered' event.
            context: Per-message context providing the knowledge graph service.
        """
        payload = event.payload
        await context.knowledge_graph.register_channel_activity(
            person_id=payload["person_id"],
            person_name=payload["person_name"],
            channel_id=payload["channel_id"],
            channel_name=payload["channel_name"],
        )
