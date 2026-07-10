"""Event publisher port — abstract interface for publishing domain events."""

from abc import ABC, abstractmethod

from app.domain.events.base import DomainEvent


class IEventPublisher(ABC):
    """Abstract interface for publishing domain events to external systems."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event."""

    @abstractmethod
    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events."""

    @abstractmethod
    async def stop(self) -> None:
        """Release any underlying connections/resources held by the publisher."""
