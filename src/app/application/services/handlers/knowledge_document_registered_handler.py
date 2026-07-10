"""Handles the inbound 'knowledge_graph.document_registered' event."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import KNOWLEDGE_DOCUMENT_REGISTERED


class KnowledgeDocumentRegisteredHandler(IInboundEventHandler):
    """Registers a document, its author, and the topics it references.

    Expected payload: document_id, title, author_id, author_name, topics[],
    url?, source?
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return KNOWLEDGE_DOCUMENT_REGISTERED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Register the document via the knowledge graph service.

        Args:
            event: The inbound 'knowledge_graph.document_registered' event.
            context: Per-message context providing the knowledge graph service.
        """
        payload = event.payload
        await context.knowledge_graph.register_document(
            document_id=payload["document_id"],
            title=payload["title"],
            author_id=payload["author_id"],
            author_name=payload["author_name"],
            topics=payload["topics"],
            url=payload.get("url"),
            source=payload.get("source"),
        )
