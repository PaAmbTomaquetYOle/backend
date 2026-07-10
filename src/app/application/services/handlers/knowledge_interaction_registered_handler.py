"""Handles the inbound 'knowledge_graph.interaction_registered' event."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import KNOWLEDGE_INTERACTION_REGISTERED


class KnowledgeInteractionRegisteredHandler(IInboundEventHandler):
    """Registers that a person interacted with a topic in the knowledge graph.

    Expected payload: person_id, person_name, topic_name, interaction_type,
    department?, topic_description?
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return KNOWLEDGE_INTERACTION_REGISTERED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Register the interaction via the knowledge graph service.

        Args:
            event: The inbound 'knowledge_graph.interaction_registered' event.
            context: Per-message context providing the knowledge graph service.
        """
        payload = event.payload
        await context.knowledge_graph.register_interaction(
            person_id=payload["person_id"],
            person_name=payload["person_name"],
            topic_name=payload["topic_name"],
            interaction_type=payload["interaction_type"],
            department=payload.get("department"),
            topic_description=payload.get("topic_description"),
        )
