"""Handles the inbound 'interview.started' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import InterviewStateEnum, OffboardingProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import INTERVIEW_STARTED


class InterviewStartedHandler(IInboundEventHandler):
    """Records that the interview for an offboarding process has begun.

    Expected payload: process_id, employee_id (employee_id is the departing
    user's ID, already known from the offboarding process — not needed here).

    Creates the interview if it doesn't exist yet and transitions it to
    IN_PROGRESS. Idempotent: if the interview is already past SCHEDULED
    (e.g. a redelivered message, or 'interview.completed' already handled
    it), the start transition is skipped instead of raising.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return INTERVIEW_STARTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Create/refresh the interview and start it if still SCHEDULED.

        Args:
            event: The inbound 'interview.started' event.
            context: Per-message context providing the offboarding facade.
        """
        facade = context.offboarding
        payload = event.payload
        process_id = OffboardingProcessId(UUID(payload["process_id"]))

        interview, _created = await facade.upsert_interview(
            process_id=process_id,
            scheduled_at=event.occurred_at,
        )
        if interview.state.get_state() == InterviewStateEnum.SCHEDULED:
            await facade.start_interview(process_id)
