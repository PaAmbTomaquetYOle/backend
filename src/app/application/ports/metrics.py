"""Metrics port — abstract interface for recording silenced-failure counters.

Every site that used to swallow a broad ``except Exception`` with only a log
line now also records a labeled counter through this port, so degradations
that never raise past their boundary (a flaky mcp-server, a Kafka hiccup, a
DLQ send failure) are still visible outside the logs (BE-20).
"""

from abc import ABC, abstractmethod
from enum import StrEnum


class FailureKind(StrEnum):
    """Category of a failure that was caught and handled rather than propagated."""

    DLQ_SEND = "dlq_send"
    EVENT_PUBLISH = "event_publish"
    DOSSIER_FALLBACK = "dossier_fallback"
    STARTUP_DEGRADED = "startup_degraded"
    NEO4J_CONNECTIVITY = "neo4j_connectivity"
    REVIEW_SWEEP = "review_sweep"


class IMetricsPort(ABC):
    """Abstract interface for recording that a handled failure occurred."""

    @abstractmethod
    def increment_failure(self, kind: FailureKind, **labels: str) -> None:
        """Record one occurrence of the given failure kind.

        Args:
            kind: The category of failure being recorded.
            labels: Additional label values (e.g. topic, event_type,
                component) attached to the counter for that occurrence.
        """
