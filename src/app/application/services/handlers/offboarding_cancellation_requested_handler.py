"""Handles the inbound 'offboarding.cancellation_requested' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import OffboardingProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import OFFBOARDING_CANCELLATION_REQUESTED


class OffboardingCancellationRequestedHandler(IInboundEventHandler):
    """Cancels an offboarding process.

    Expected payload: process_id.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return OFFBOARDING_CANCELLATION_REQUESTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Cancel the offboarding process referenced by the payload.

        Args:
            event: The inbound 'offboarding.cancellation_requested' event.
            context: Per-message context providing the offboarding facade.
        """
        payload = event.payload
        process_id = OffboardingProcessId(UUID(payload["process_id"]))
        await context.offboarding.cancel_offboarding(process_id)
