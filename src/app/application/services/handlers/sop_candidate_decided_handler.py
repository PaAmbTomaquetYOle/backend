"""Handles the inbound 'sop.candidate_decided' event (SA-16)."""

import logging

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import SOP_CANDIDATE_DECIDED
from app.domain.exceptions.sops import (
    InvalidSopCandidateTransitionError,
    SopCandidateNotFoundError,
)
from app.domain.sops.id import ChannelId

logger = logging.getLogger(__name__)


class SopCandidateDecidedHandler(IInboundEventHandler):
    """Records the author's accept/reject decision for an offered SOP candidate.

    Expected payload: channel_id, message_ts, accepted.

    The actual SOP is created by the existing 'sop.creation_requested' flow
    when the author accepts — this handler only tracks the candidate's own
    lifecycle. A missing candidate or a redelivered/duplicate decision is
    logged and dropped rather than sent to the DLQ: both are expected races
    (Kafka delivery across topics is unordered, and at-least-once delivery
    can redeliver a decision already applied), not message corruption.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return SOP_CANDIDATE_DECIDED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Apply the decision via the SOP candidate service.

        Args:
            event: The inbound 'sop.candidate_decided' event.
            context: Per-message context providing the SOP candidate service.
        """
        payload = event.payload
        channel_id = ChannelId(payload["channel_id"])
        message_ts = payload["message_ts"]
        try:
            await context.sop_candidates.record_decision(
                channel_id=channel_id,
                message_ts=message_ts,
                accepted=payload["accepted"],
            )
        except SopCandidateNotFoundError:
            logger.warning(
                "sop.candidate_decided for unknown candidate %s:%s; dropping",
                payload["channel_id"],
                message_ts,
            )
        except InvalidSopCandidateTransitionError:
            logger.warning(
                "sop.candidate_decided redelivered for already-decided candidate %s:%s; dropping",
                payload["channel_id"],
                message_ts,
            )
