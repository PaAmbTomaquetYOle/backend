"""Handles the inbound 'monthly_review.triggered' event."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain import EmployeeId, ManagerId, MonthlyReviewProcessStateEnum
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import MONTHLY_REVIEW_TRIGGERED

_ACTIVE_STATES = (
    MonthlyReviewProcessStateEnum.NOT_STARTED,
    MonthlyReviewProcessStateEnum.IN_PROGRESS,
)


class MonthlyReviewTriggeredHandler(IInboundEventHandler):
    """Creates a new monthly review process and starts it.

    Expected payload: employee_id, manager_id, employee_name?, manager_name?

    Idempotent: if an active (not yet finished/cancelled) process already
    exists for the employee — e.g. a redelivered message — that process is
    reused instead of creating a duplicate.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return MONTHLY_REVIEW_TRIGGERED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Get-or-create the monthly review process and transition it to IN_PROGRESS.

        Args:
            event: The inbound 'monthly_review.triggered' event.
            context: Per-message context providing the monthly review facade.
        """
        payload = event.payload
        facade = context.monthly_review
        employee_id = EmployeeId(payload["employee_id"])

        existing = await facade.list_reviews(employee_id=employee_id)
        active = [p for p in existing if p.state_value in _ACTIVE_STATES]
        process = active[0] if active else None

        if process is None:
            process = await facade.create_review(
                employee_id=employee_id,
                manager_id=ManagerId(payload["manager_id"]),
                employee_name=payload.get("employee_name"),
                manager_name=payload.get("manager_name"),
            )

        if process.state_value == MonthlyReviewProcessStateEnum.NOT_STARTED:
            await facade.start_review(process.process_id)
