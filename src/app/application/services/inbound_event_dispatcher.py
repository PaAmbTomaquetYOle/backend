"""Dispatches inbound domain events to their registered handler."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.events.base import DomainEvent


class UnknownEventTypeError(ValueError):
    """Raised when no handler is registered for an event's event_type."""


class InboundEventDispatcher:
    """Routes a DomainEvent to the IInboundEventHandler registered for its event_type.

    Adding support for a new inbound event means adding a new IInboundEventHandler
    and registering it here — existing handlers are never touched (Open/Closed).
    """

    def __init__(self, handlers: list[IInboundEventHandler]) -> None:
        """Build the dispatch table from the given handlers.

        Args:
            handlers: The handlers to register, one per supported event_type.

        Raises:
            ValueError: If two handlers register the same event_type.
        """
        self._handlers: dict[str, IInboundEventHandler] = {}
        for handler in handlers:
            if handler.event_type in self._handlers:
                raise ValueError(f"Duplicate handler for event_type '{handler.event_type}'")
            self._handlers[handler.event_type] = handler

    async def dispatch(self, event: DomainEvent, context: InboundContext) -> None:
        """Route the event to its registered handler.

        Args:
            event: The inbound domain event to process.
            context: The per-message context passed through to the handler.

        Raises:
            UnknownEventTypeError: If no handler is registered for event.event_type.
        """
        handler = self._handlers.get(event.event_type)
        if handler is None:
            raise UnknownEventTypeError(
                f"No handler registered for event_type '{event.event_type}'"
            )
        await handler.handle(event, context)
