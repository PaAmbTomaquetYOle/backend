"""Tests for the metrics port's concrete adapters (BE-20)."""

from app.application.ports.metrics import FailureKind
from app.infrastructure.adapters.metrics.noop_metrics import NoOpMetrics
from app.infrastructure.adapters.metrics.prometheus_metrics import (
    _SILENCED_FAILURES,
    PrometheusMetricsAdapter,
)


class TestNoOpMetrics:
    def test_increment_failure_is_a_noop(self) -> None:
        metrics = NoOpMetrics()
        metrics.increment_failure(FailureKind.DLQ_SEND, topic="x")  # must not raise


class TestPrometheusMetricsAdapter:
    def test_increment_failure_increments_the_counter_for_its_kind(self) -> None:
        adapter = PrometheusMetricsAdapter()
        before = _SILENCED_FAILURES.labels(
            kind=FailureKind.EVENT_PUBLISH.value, detail="event_type=x"
        )._value.get()

        adapter.increment_failure(FailureKind.EVENT_PUBLISH, event_type="x")

        after = _SILENCED_FAILURES.labels(
            kind=FailureKind.EVENT_PUBLISH.value, detail="event_type=x"
        )._value.get()
        assert after == before + 1

    def test_labels_are_sorted_into_a_stable_detail_string(self) -> None:
        adapter = PrometheusMetricsAdapter()
        before = _SILENCED_FAILURES.labels(
            kind=FailureKind.DLQ_SEND.value, detail="dlq_topic=dlq,source_topic=src"
        )._value.get()

        adapter.increment_failure(FailureKind.DLQ_SEND, source_topic="src", dlq_topic="dlq")

        after = _SILENCED_FAILURES.labels(
            kind=FailureKind.DLQ_SEND.value, detail="dlq_topic=dlq,source_topic=src"
        )._value.get()
        assert after == before + 1
