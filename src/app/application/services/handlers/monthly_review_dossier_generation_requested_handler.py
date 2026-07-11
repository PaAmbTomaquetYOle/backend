"""Handles the inbound 'monthly_review.dossier_generation_requested' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import MonthlyReviewProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED


class MonthlyReviewDossierGenerationRequestedHandler(IInboundEventHandler):
    """Generates and persists the dossier for a process, then completes it.

    Expected payload: process_id. The interview content is read from the
    database (source of truth), not carried in the payload.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return MONTHLY_REVIEW_DOSSIER_GENERATION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Generate the dossier and complete the monthly review process.

        Args:
            event: The inbound 'monthly_review.dossier_generation_requested' event.
            context: Per-message context providing the monthly review facade.
        """
        process_id = MonthlyReviewProcessId(UUID(event.payload["process_id"]))
        await context.monthly_review.generate_dossier(process_id)
