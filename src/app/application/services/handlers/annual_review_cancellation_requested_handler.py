"""Handles the inbound 'annual_review.cancellation_requested' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import AnnualReviewProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import ANNUAL_REVIEW_CANCELLATION_REQUESTED


class AnnualReviewCancellationRequestedHandler(IInboundEventHandler):
    """Cancels an annual review process.

    Expected payload: process_id.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return ANNUAL_REVIEW_CANCELLATION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Cancel the annual review process referenced by the payload.

        Args:
            event: The inbound 'annual_review.cancellation_requested' event.
            context: Per-message context providing the annual review facade.
        """
        payload = event.payload
        process_id = AnnualReviewProcessId(UUID(payload["process_id"]))
        await context.annual_review.cancel_review(process_id)
