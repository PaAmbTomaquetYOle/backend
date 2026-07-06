"""Inbound event handler port — one handler per recognized event type (OCP)."""

from abc import ABC, abstractmethod

from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.domain.events.base import DomainEvent


class IInboundEventHandler(ABC):
    """Abstract interface for a handler that reacts to one inbound event type.

    Each concrete handler owns exactly one ``event_type`` and the business
    logic to run for it. New inbound events are supported by adding a new
    handler and registering it with the dispatcher, without modifying
    existing handlers (Open/Closed Principle).
    """

    @property
    @abstractmethod
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""

    @abstractmethod
    async def handle(self, event: DomainEvent, facade: IOffboardingServiceFacade) -> None:
        """Execute the business logic for this event.

        Args:
            event: The deserialized inbound domain event.
            facade: The offboarding facade, composed fresh per message, used to
                invoke the relevant use case(s).
        """
