"""Handles the inbound 'monthly_review.interview_completed' event."""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.handlers._turn_payload import turn_from_payload
from app.application.services.inbound_context import InboundContext
from app.domain import InterviewStateEnum, MonthlyReviewProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_INTERVIEW_COMPLETED


class MonthlyReviewInterviewCompletedHandler(IInboundEventHandler):
    """Persists the interview's answers and advances the interview's state.

    Expected payload: process_id, turns[] (turn_type, speaker_role, timestamp,
    content, order, topic?, sentiment?, answer_text?).

    Unlike offboarding, this does not submit the process anywhere:
    MonthlyReviewProcess has no PENDING_REVISION state — it stays IN_PROGRESS
    until 'monthly_review.dossier_generation_requested' completes it directly.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return MONTHLY_REVIEW_INTERVIEW_COMPLETED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Save the collected answers and transition the interview forward.

        Args:
            event: The inbound 'monthly_review.interview_completed' event.
            context: Per-message context providing the monthly review facade.
        """
        facade = context.monthly_review
        payload = event.payload
        process_id = MonthlyReviewProcessId(UUID(payload["process_id"]))
        turns = [turn_from_payload(raw) for raw in payload.get("turns", [])]

        interview, _created = await facade.upsert_interview(
            process_id=process_id,
            scheduled_at=event.occurred_at,
            turns=turns,
        )
        if interview.state.get_state() == InterviewStateEnum.SCHEDULED:
            await facade.start_interview(process_id)
        await facade.complete_interview(process_id)
