"""Tests for the ObservedOperation template method (BE-20)."""

from unittest.mock import Mock

import pytest

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.metrics import FailureKind


class _SucceedingOperation(ObservedOperation[str]):
    async def _execute(self) -> str:
        return "ok"

    def _failure_kind(self) -> FailureKind:
        return FailureKind.EVENT_PUBLISH

    async def _recover(self, exc: Exception) -> str:
        return "recovered"


class _FailingOperation(ObservedOperation[str]):
    def __init__(self, metrics, exc: Exception) -> None:
        super().__init__(metrics)
        self._exc = exc
        self.logged: Exception | None = None
        self.recovered_from: Exception | None = None

    async def _execute(self) -> str:
        raise self._exc

    def _failure_kind(self) -> FailureKind:
        return FailureKind.DOSSIER_FALLBACK

    def _labels(self) -> dict[str, str]:
        return {"scope": "offboarding"}

    def _log_failure(self, exc: Exception) -> None:
        self.logged = exc

    async def _recover(self, exc: Exception) -> str:
        self.recovered_from = exc
        return "recovered"


class _NarrowingOperation(_FailingOperation):
    def _expected_exceptions(self) -> tuple[type[Exception], ...]:
        return (ValueError,)


class TestObservedOperation:
    @pytest.mark.anyio
    async def test_run_returns_execute_result_when_no_failure(self) -> None:
        result = await _SucceedingOperation(Mock()).run()
        assert result == "ok"

    @pytest.mark.anyio
    async def test_run_recovers_and_records_metric_on_expected_failure(self) -> None:
        metrics = Mock()
        exc = RuntimeError("boom")
        operation = _FailingOperation(metrics, exc)

        result = await operation.run()

        assert result == "recovered"
        assert operation.logged is exc
        assert operation.recovered_from is exc
        metrics.increment_failure.assert_called_once_with(
            FailureKind.DOSSIER_FALLBACK, scope="offboarding"
        )

    @pytest.mark.anyio
    async def test_run_skips_metric_when_metrics_is_none(self) -> None:
        operation = _FailingOperation(None, RuntimeError("boom"))

        result = await operation.run()  # must not raise despite metrics=None

        assert result == "recovered"

    @pytest.mark.anyio
    async def test_narrowed_operation_lets_unexpected_exception_types_propagate(self) -> None:
        operation = _NarrowingOperation(Mock(), RuntimeError("not a ValueError"))

        with pytest.raises(RuntimeError):
            await operation.run()

    @pytest.mark.anyio
    async def test_narrowed_operation_catches_expected_exception_type(self) -> None:
        metrics = Mock()
        operation = _NarrowingOperation(metrics, ValueError("expected"))

        result = await operation.run()

        assert result == "recovered"
        metrics.increment_failure.assert_called_once()
