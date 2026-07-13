"""Handles the inbound 'interview.turn_recorded' event (SA-16).

Persists interview turns incrementally as slack-agent's in-memory session
accumulates them, instead of only receiving the full turn list at
'interview.completed'. This closes the durability gap where a slack-agent
restart mid-interview used to lose every unsent turn.
"""

from uuid import UUID

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.handlers._turn_payload import turn_from_payload
from app.application.services.inbound_context import InboundContext
from app.domain import InterviewStateEnum, OffboardingProcessId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import INTERVIEW_TURN_RECORDED
from app.domain.exceptions.interview import InterviewNotFoundError


class InterviewTurnRecordedHandler(IInboundEventHandler):
    """Appends newly recorded turns to the process's interview.

    Expected payload: process_id, turns[] (turn_type, speaker_role, timestamp,
    content, order, topic?, sentiment?, answer_text?).

    Kafka delivery across topics is not ordered, so this handler is defensive
    about arriving before 'interview.started' or 'interview.completed':
    - Creates the interview (SCHEDULED, empty) if none exists yet for the process.
    - Starts it if it's still SCHEDULED.
    - Skips turns whose order is already persisted (at-least-once redelivery, or
      'interview.completed' having already replaced the full turn set — in which
      case this event is stale and its turns are already covered).

    If the interview turns out to already be COMPLETED/CANCELLED, appending is
    not possible (interview.add_turn requires IN_PROGRESS); the turns are
    dropped since 'interview.completed' already carries the authoritative full
    turn list for that case.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return INTERVIEW_TURN_RECORDED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Append any not-yet-persisted turns to the process's interview.

        Args:
            event: The inbound 'interview.turn_recorded' event.
            context: Per-message context providing the offboarding facade.
        """
        facade = context.offboarding
        payload = event.payload
        process_id = OffboardingProcessId(UUID(payload["process_id"]))
        turns = [turn_from_payload(raw) for raw in payload.get("turns", [])]
        if not turns:
            return

        try:
            interview = await facade.get_interview(process_id)
        except InterviewNotFoundError:
            interview, _created = await facade.upsert_interview(
                process_id=process_id,
                scheduled_at=event.occurred_at,
            )

        if interview.state.get_state() == InterviewStateEnum.SCHEDULED:
            interview = await facade.start_interview(process_id)

        if interview.state.get_state() != InterviewStateEnum.IN_PROGRESS:
            return

        already_persisted_orders = {turn.order for turn in interview.turns}
        new_turns = [turn for turn in turns if turn.order not in already_persisted_orders]
        if new_turns:
            await facade.add_interview_turns(process_id, new_turns)
