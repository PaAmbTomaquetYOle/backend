"""Template method for a fallible operation whose failure must never be silent.

Before BE-20, every site that swallowed a broad ``except Exception`` repeated
the same shape: try the risky call, log the failure, and recover somehow
(re-raise, fall back to a default, or just swallow). ``ObservedOperation``
fixes that skeleton in one place — ``run()`` is the template method — and
pushes the part that legitimately varies per call site (which exceptions are
expected, how to log them, what metric to record, how to recover) into hooks
that subclasses override, instead of duplicating try/except everywhere.
"""

import logging
from abc import ABC, abstractmethod

from app.application.ports.metrics import FailureKind, IMetricsPort

logger = logging.getLogger(__name__)


class ObservedOperation[T](ABC):
    """Runs `_execute`, observing (logging + metric) and recovering from failure."""

    def __init__(self, metrics: IMetricsPort | None) -> None:
        """Set up the operation with the metrics port used to record a failure.

        Args:
            metrics: Port used to increment a counter when `_execute` fails.
                Optional like every other collaborator port in this codebase
                (`IEventPublisher`, `IDossierGenerator`) — `None` means the
                caller wasn't wired with a metrics adapter (e.g. a unit test
                exercising the service directly), so recording is skipped
                rather than requiring every call site to inject a no-op.
        """
        self._metrics = metrics

    async def run(self) -> T:
        """Execute the operation, observing and recovering from any expected failure.

        Returns:
            T: The result of `_execute`, or of `_recover` if it failed.
        """
        try:
            return await self._execute()
        except self._expected_exceptions() as exc:
            self._log_failure(exc)
            if self._metrics is not None:
                self._metrics.increment_failure(self._failure_kind(), **self._labels())
            return await self._recover(exc)

    @abstractmethod
    async def _execute(self) -> T:
        """Run the risky operation. Raises on failure."""

    @abstractmethod
    def _failure_kind(self) -> FailureKind:
        """The metric category to record when `_execute` fails."""

    @abstractmethod
    async def _recover(self, exc: Exception) -> T:
        """Handle a caught failure: re-raise, fall back to a default, or swallow it."""

    def _expected_exceptions(self) -> tuple[type[Exception], ...]:
        """Exception types this operation narrows its catch to.

        Defaults to the broadest catch; override to narrow to the concrete
        failure modes of the wrapped operation (e.g. KafkaError, Neo4jError).
        A subclass that keeps the broad default must explain why in a
        docstring/comment — see DossierGenerationOperation for an example.
        """
        return (Exception,)

    def _labels(self) -> dict[str, str]:
        """Extra label values attached to the recorded metric. Override to add context."""
        return {}

    def _log_failure(self, exc: Exception) -> None:
        """Log the caught failure. Override to control level, message, and context."""
        logger.warning("%s failed", type(self).__name__, exc_info=True)
