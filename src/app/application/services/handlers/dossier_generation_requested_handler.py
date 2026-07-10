"""Handles the inbound 'dossier.generation_requested' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import OffboardingProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import DOSSIER_GENERATION_REQUESTED


class DossierGenerationRequestedHandler(IInboundEventHandler):
    """Generates and persists the dossier for a process, then completes it.

    Expected payload: process_id. The interview content is read from the
    database (source of truth), not carried in the payload.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return DOSSIER_GENERATION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Generate the dossier and close out the offboarding process.

        Args:
            event: The inbound 'dossier.generation_requested' event.
            context: Per-message context providing the offboarding facade.
        """
        process_id = OffboardingProcessId(UUID(event.payload["process_id"]))
        await context.offboarding.generate_dossier(process_id)
