"""Handles the inbound 'offboarding.triggered' event."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.domain import EmployeeId, ManagerId
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import OFFBOARDING_TRIGGERED


class OffboardingTriggeredHandler(IInboundEventHandler):
    """Creates a new offboarding process and starts it.

    Expected payload: employee_id, manager_id, employee_name?, manager_name?
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return OFFBOARDING_TRIGGERED

    async def handle(self, event: DomainEvent, facade: IOffboardingServiceFacade) -> None:
        """Create the offboarding process and transition it to IN_PROGRESS.

        Args:
            event: The inbound 'offboarding.triggered' event.
            facade: The offboarding facade used to run the use case.
        """
        payload = event.payload
        process = await facade.create_offboarding(
            employee_id=EmployeeId(payload["employee_id"]),
            manager_id=ManagerId(payload["manager_id"]),
            employee_name=payload.get("employee_name"),
            manager_name=payload.get("manager_name"),
        )
        await facade.start_offboarding(process.process_id)
