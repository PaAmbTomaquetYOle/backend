"""Handles the inbound 'monthly_review.cancellation_requested' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import MonthlyReviewProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_CANCELLATION_REQUESTED


class MonthlyReviewCancellationRequestedHandler(IInboundEventHandler):
    """Cancels a monthly review process.

    Expected payload: process_id.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return MONTHLY_REVIEW_CANCELLATION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Cancel the monthly review process referenced by the payload.

        Args:
            event: The inbound 'monthly_review.cancellation_requested' event.
            context: Per-message context providing the monthly review facade.
        """
        payload = event.payload
        process_id = MonthlyReviewProcessId(UUID(payload["process_id"]))
        await context.monthly_review.cancel_review(process_id)
