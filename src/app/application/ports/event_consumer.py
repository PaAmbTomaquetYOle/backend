"""Event consumer port — abstract interface for a background inbound-event listener."""

from abc import ABC, abstractmethod


class IEventConsumer(ABC):
    """Abstract interface for a component that consumes domain events from an
    external system and dispatches them to application logic.

    Mirrors IEventPublisher's role on the outbound side, but as a background
    process with its own lifecycle (started/stopped alongside the app), rather
    than something called synchronously per request.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start consuming events in the background."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop consuming events and release any underlying resources."""
