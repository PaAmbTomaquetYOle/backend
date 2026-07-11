"""Dead-letter queue port — abstract interface for parking unprocessable messages."""

from abc import ABC, abstractmethod


class IDeadLetterQueue(ABC):
    """Abstract interface for routing a message that could not be processed
    (malformed payload or handler failure) so it does not block or crash the
    consumer, and can be inspected/reprocessed later.
    """

    @abstractmethod
    async def send(self, raw_value: bytes, source_topic: str, error: Exception) -> None:
        """Send an unprocessable message to the dead-letter destination.

        Args:
            raw_value: The original, undeserialized message payload.
            source_topic: The topic the message was originally consumed from.
            error: The exception raised while parsing or handling the message.

        Raises:
            Exception: If the send to the dead-letter destination itself
                fails (BE-20). Implementations must let this propagate
                rather than swallow it: the caller relies on the failure to
                decide not to commit the source offset, so a failed DLQ send
                does not silently drop the original message.
        """
