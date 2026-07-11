"""Unit tests for ReviewScheduler (BE-24)."""

from __future__ import annotations

import pytest

from app.infrastructure.scheduling.review_scheduler import ReviewScheduler


class TestReviewSchedulerLifecycle:
    @pytest.mark.anyio
    async def test_start_registers_job_and_starts_scheduler(self) -> None:
        scheduler = ReviewScheduler(hour_utc=3)

        scheduler.start()
        try:
            assert scheduler._scheduler.running
            assert scheduler._scheduler.get_job("review_scheduling_sweep") is not None
        finally:
            scheduler.stop()

    def test_stop_is_a_noop_when_never_started(self) -> None:
        scheduler = ReviewScheduler(hour_utc=3)
        scheduler.stop()  # must not raise

    @pytest.mark.anyio
    async def test_stop_after_start_shuts_down_cleanly(self) -> None:
        scheduler = ReviewScheduler(hour_utc=3)
        scheduler.start()

        scheduler.stop()  # must not raise


class TestReviewSchedulerSweep:
    @pytest.mark.anyio
    async def test_sweep_failure_is_caught_and_logged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failing sweep (e.g. DB unreachable) must not raise out of the job."""
        from app.infrastructure.scheduling import review_scheduler as module

        def _raise_engine(*args, **kwargs):
            raise RuntimeError("db unreachable")

        monkeypatch.setattr(module, "get_engine", _raise_engine)
        scheduler = ReviewScheduler(hour_utc=3)

        await scheduler._run_sweep()  # must not raise
