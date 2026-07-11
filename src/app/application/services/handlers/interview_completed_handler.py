"""Handles the inbound 'interview.completed' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.handlers._turn_payload import turn_from_payload
from app.application.services.inbound_context import InboundContext
from app.domain import InterviewStateEnum, OffboardingProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import INTERVIEW_COMPLETED


class InterviewCompletedHandler(IInboundEventHandler):
    """Persists the interview's answers and advances process/interview state.

    Expected payload: process_id, turns[] (turn_type, speaker_role, timestamp,
    content, order, topic?, sentiment?, answer_text?).

    The interview is only started here if it's still SCHEDULED — if
    'interview.started' already moved it to IN_PROGRESS, that step is skipped.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return INTERVIEW_COMPLETED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Save the collected answers and transition interview/process forward.

        Args:
            event: The inbound 'interview.completed' event.
            context: Per-message context providing the offboarding facade.
        """
        facade = context.offboarding
        payload = event.payload
        process_id = OffboardingProcessId(UUID(payload["process_id"]))
        turns = [turn_from_payload(raw) for raw in payload.get("turns", [])]

        interview, _created = await facade.upsert_interview(
            process_id=process_id,
            scheduled_at=event.occurred_at,
            turns=turns,
        )
        if interview.state.get_state() == InterviewStateEnum.SCHEDULED:
            await facade.start_interview(process_id)
        await facade.complete_interview(process_id)
        await facade.submit_offboarding_for_review(process_id)
