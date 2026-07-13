"""No-op implementation of IEventPublisher for tests and local dev."""

from app.application.ports.event_publisher import IEventPublisher
from app.domain.events.base import DomainEvent


class NoOpEventPublisher(IEventPublisher):
    """Silently discards all events. Used when Kafka is not configured."""

    async def publish(self, event: DomainEvent) -> None:
        pass

    async def publish_many(self, events: list[DomainEvent]) -> None:
        pass

    async def stop(self) -> None:
        pass
