"""AIOKafkaConsumer-based implementation of IEventConsumer."""

import asyncio
import contextlib
import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import ConsumerRecord
from sqlmodel import Session

from app.application.ports.dead_letter_queue import IDeadLetterQueue
from app.application.ports.dossier_generator import IDossierGenerator
from app.application.ports.event_consumer import IEventConsumer
from app.application.ports.event_publisher import IEventPublisher
from app.application.services.inbound_event_dispatcher import InboundEventDispatcher
from app.infrastructure.adapters.events.event_deserializer import (
    EventDeserializationError,
    deserialize_event,
)
from app.infrastructure.composition import build_offboarding_facade
from app.infrastructure.persistence.database import get_engine

logger = logging.getLogger(__name__)


class KafkaEventConsumer(IEventConsumer):
    """Consumes inbound domain events from Kafka and dispatches them to application logic.

    Runs its own background asyncio task, mirroring how AIOKafkaProducer is
    started/stopped alongside the app in the lifespan. Offsets are committed
    manually (enable_auto_commit=False on the wrapped consumer) only after a
    message has been successfully dispatched, or routed to the dead-letter
    queue — so a crash mid-processing causes at most a redelivery, never a
    silent skip. A malformed message or a handler failure never propagates
    out of the loop: it is logged and sent to the DLQ instead.
    """

    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        dispatcher: InboundEventDispatcher,
        dead_letter_queue: IDeadLetterQueue,
        event_publisher: IEventPublisher | None = None,
        dossier_generator: IDossierGenerator | None = None,
    ) -> None:
        self._consumer = consumer
        self._dispatcher = dispatcher
        self._dlq = dead_letter_queue
        self._event_publisher = event_publisher
        self._dossier_generator = dossier_generator
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the underlying AIOKafkaConsumer and the background consume loop."""
        await self._consumer.start()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Cancel the background loop and stop the underlying AIOKafkaConsumer."""
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._consumer.stop()

    async def _run(self) -> None:
        """Consume messages until cancelled, processing each one in turn."""
        async for message in self._consumer:
            await self._process(message)

    async def _process(self, message: ConsumerRecord) -> None:
        """Deserialize, dispatch, and commit a single Kafka message.

        Args:
            message: The raw Kafka message consumed from a subscribed topic.
        """
        try:
            event = deserialize_event(message.value)
        except EventDeserializationError as exc:
            logger.warning(
                "Malformed event on topic %s, routing to DLQ", message.topic, exc_info=True
            )
            await self._dlq.send(message.value, message.topic, exc)
            await self._consumer.commit()
            return

        try:
            with Session(get_engine()) as session:
                facade = build_offboarding_facade(
                    session, self._event_publisher, self._dossier_generator
                )
                await self._dispatcher.dispatch(event, facade)
        except Exception as exc:
            logger.warning(
                "Failed to process event %s from topic %s, routing to DLQ",
                event.event_type,
                message.topic,
                exc_info=True,
            )
            await self._dlq.send(message.value, message.topic, exc)

        await self._consumer.commit()
