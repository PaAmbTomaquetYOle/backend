"""Shared ObservedOperation for the defensive event-publish step used by every facade."""

import logging

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.metrics import FailureKind, IMetricsPort
from app.domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class EventPublishOperation(ObservedOperation[None]):
    """Publishes one domain event, never letting a publish failure break the use case.

    Kept broad (`Exception`, the base default) on purpose: `IEventPublisher`
    is an abstraction over any transport (Kafka today, something else
    tomorrow), so this call site cannot narrow to a concrete driver's
    exception type without leaking an infrastructure concern into the
    application layer. Narrowing happens one layer down, in the concrete
    adapter (e.g. `KafkaEventPublisher`, `KafkaPublishOperation`).
    """

    def __init__(
        self, metrics: IMetricsPort | None, publisher: IEventPublisher, event: DomainEvent
    ) -> None:
        """Set up the operation with the metrics port, publisher, and event to publish.

        Args:
            metrics: Port used to record a failure if publishing fails.
            publisher: The event publisher the event is sent through.
            event: The domain event to publish.
        """
        super().__init__(metrics)
        self._publisher = publisher
        self._event = event

    async def _execute(self) -> None:
        await self._publisher.publish(self._event)

    def _failure_kind(self) -> FailureKind:
        return FailureKind.EVENT_PUBLISH

    def _labels(self) -> dict[str, str]:
        return {"event_type": self._event.event_type}

    def _log_failure(self, exc: Exception) -> None:
        logger.warning("Failed to publish event %s", self._event.event_type, exc_info=True)

    async def _recover(self, exc: Exception) -> None:
        return None
