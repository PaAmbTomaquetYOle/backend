"""Prometheus implementation of IMetricsPort."""

from prometheus_client import Counter

from app.application.ports.metrics import FailureKind, IMetricsPort

_SILENCED_FAILURES = Counter(
    "offboardme_silenced_failures_total",
    "Count of failures that were caught and handled (not propagated) by kind.",
    labelnames=("kind", "detail"),
)


class PrometheusMetricsAdapter(IMetricsPort):
    """Records handled failures as a labeled Prometheus counter.

    A single counter is used for every failure kind, labeled by ``kind`` and
    a ``detail`` string built from whatever extra labels the call site
    supplies (e.g. topic, event_type, component) — this keeps the exposed
    metric's label set fixed while still letting each call site attach its
    own bounded context.
    """

    def increment_failure(self, kind: FailureKind, **labels: str) -> None:
        detail = ",".join(f"{key}={value}" for key, value in sorted(labels.items()))
        _SILENCED_FAILURES.labels(kind=kind.value, detail=detail).inc()
