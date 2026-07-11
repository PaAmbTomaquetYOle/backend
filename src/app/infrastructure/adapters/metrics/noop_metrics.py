"""No-op implementation of IMetricsPort for tests and when metrics are disabled."""

from app.application.ports.metrics import FailureKind, IMetricsPort


class NoOpMetrics(IMetricsPort):
    """Discards every recorded failure. Used when METRICS_ENABLED is false."""

    def increment_failure(self, kind: FailureKind, **labels: str) -> None:
        pass
