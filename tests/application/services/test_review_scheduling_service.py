"""Unit tests for ReviewSchedulingService (BE-24)."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.application.service_interfaces.annual_review_facade_interface import (
    IAnnualReviewServiceFacade,
)
from app.application.service_interfaces.monthly_review_facade_interface import (
    IMonthlyReviewServiceFacade,
)
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.services.review_scheduling_service import ReviewSchedulingService
from app.domain import (
    AnnualReviewProcess,
    AnnualReviewProcessId,
    MonthlyReviewProcess,
    MonthlyReviewProcessId,
    OffboardingProcess,
    OffboardingProcessId,
)
from app.domain.annual_review.state.finished import FinishedState as AnnualFinishedState
from app.domain.annual_review.state.in_progress import InProgressState as AnnualInProgressState
from app.domain.annual_review.state.not_started import NotStartedState as AnnualNotStartedState
from app.domain.monthly_review.state.finished import FinishedState as MonthlyFinishedState
from app.domain.monthly_review.state.in_progress import InProgressState as MonthlyInProgressState
from app.domain.offboarding.id import EmployeeId, ManagerId
from app.domain.offboarding.state.finished import FinishedState as OffboardingFinishedState

NOW = datetime(2026, 7, 11, 12, 0, 0)


def _offboarding(employee_id: str, created_at: datetime, state=None) -> OffboardingProcess:
    return OffboardingProcess(
        process_id=OffboardingProcessId(),
        state=state or OffboardingFinishedState(),
        employee_id=EmployeeId(employee_id),
        manager_id=ManagerId("MGR"),
        created_at=created_at,
        employee_name="Employee",
        manager_name="Manager",
    )


def _monthly(employee_id: str, created_at: datetime, state) -> MonthlyReviewProcess:
    return MonthlyReviewProcess(
        process_id=MonthlyReviewProcessId(),
        state=state,
        employee_id=EmployeeId(employee_id),
        manager_id=ManagerId("MGR"),
        created_at=created_at,
        employee_name="Employee",
        manager_name="Manager",
    )


def _annual(employee_id: str, created_at: datetime, state) -> AnnualReviewProcess:
    return AnnualReviewProcess(
        process_id=AnnualReviewProcessId(),
        state=state,
        employee_id=EmployeeId(employee_id),
        manager_id=ManagerId("MGR"),
        created_at=created_at,
        employee_name="Employee",
        manager_name="Manager",
    )


def make_facades(offboarding=None, monthly=None, annual=None):
    offboarding_facade = AsyncMock(spec=IOffboardingServiceFacade)
    offboarding_facade.list_offboardings.return_value = offboarding or []
    monthly_facade = AsyncMock(spec=IMonthlyReviewServiceFacade)
    monthly_facade.list_reviews.return_value = monthly or []
    annual_facade = AsyncMock(spec=IAnnualReviewServiceFacade)
    annual_facade.list_reviews.return_value = annual or []
    return offboarding_facade, monthly_facade, annual_facade


class TestReviewSchedulingService:
    @pytest.mark.anyio
    async def test_starts_monthly_review_when_last_finished_review_over_30_days_ago(self) -> None:
        offboarding, monthly, annual = make_facades(
            monthly=[_monthly("U1", NOW - timedelta(days=40), MonthlyFinishedState())],
        )
        created = _monthly("U1", NOW, MonthlyFinishedState())
        monthly.create_review.return_value = created
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        monthly.create_review.assert_awaited_once()
        _, kwargs = monthly.create_review.call_args
        assert kwargs["employee_id"].is_equal("U1")
        monthly.start_review.assert_awaited_once_with(created.process_id)
        assert result.monthly_started == [created.process_id]
        assert result.annual_started == []

    @pytest.mark.anyio
    async def test_skips_monthly_review_when_last_review_recent(self) -> None:
        offboarding, monthly, annual = make_facades(
            monthly=[_monthly("U1", NOW - timedelta(days=5), MonthlyFinishedState())],
        )
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        monthly.create_review.assert_not_awaited()
        assert result.monthly_started == []

    @pytest.mark.anyio
    async def test_skips_monthly_review_when_already_active(self) -> None:
        offboarding, monthly, annual = make_facades(
            monthly=[
                _monthly("U1", NOW - timedelta(days=40), MonthlyFinishedState()),
                _monthly("U1", NOW - timedelta(days=1), MonthlyInProgressState()),
            ],
        )
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        monthly.create_review.assert_not_awaited()
        assert result.monthly_started == []

    @pytest.mark.anyio
    async def test_skips_all_reviews_for_employee_who_has_left(self) -> None:
        offboarding, monthly, annual = make_facades(
            offboarding=[_offboarding("U1", NOW - timedelta(days=1000))],
            monthly=[_monthly("U1", NOW - timedelta(days=1000), MonthlyFinishedState())],
        )
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        monthly.create_review.assert_not_awaited()
        assert result.monthly_started == []

    @pytest.mark.anyio
    async def test_not_started_annual_review_counts_as_active(self) -> None:
        """A NOT_STARTED annual process is still active — it must block
        re-scheduling even though its created_at is over a year old."""
        offboarding, monthly, annual = make_facades(
            annual=[_annual("U1", NOW - timedelta(days=400), AnnualNotStartedState())],
        )
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        annual.create_review.assert_not_awaited()
        assert result.annual_started == []

    @pytest.mark.anyio
    async def test_starts_annual_review_when_last_finished_review_over_a_year_ago(self) -> None:
        offboarding, monthly, annual = make_facades(
            annual=[_annual("U1", NOW - timedelta(days=400), AnnualFinishedState())],
        )
        created = _annual("U1", NOW, AnnualNotStartedState())
        annual.create_review.return_value = created
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        annual.create_review.assert_awaited_once()
        annual.start_review.assert_awaited_once_with(created.process_id)
        assert result.annual_started == [created.process_id]

    @pytest.mark.anyio
    async def test_pending_revision_annual_review_counts_as_active(self) -> None:
        from app.domain.annual_review.state.pending_revision import PendingRevisionState

        offboarding, monthly, annual = make_facades(
            annual=[_annual("U1", NOW - timedelta(days=400), PendingRevisionState())],
        )
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        annual.create_review.assert_not_awaited()
        assert result.annual_started == []

    @pytest.mark.anyio
    async def test_active_annual_process_used_as_join_date_when_no_other_process_exists(
        self,
    ) -> None:
        """A brand-new employee with only an active annual process isn't due for
        monthly review yet (joined recently), even though they have no offboarding
        or monthly history at all."""
        offboarding, monthly, annual = make_facades(
            annual=[_annual("U1", NOW - timedelta(days=1), AnnualInProgressState())],
        )
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        monthly.create_review.assert_not_awaited()
        assert result.monthly_started == []

    @pytest.mark.anyio
    async def test_no_known_employees_returns_empty_result(self) -> None:
        offboarding, monthly, annual = make_facades()
        service = ReviewSchedulingService(offboarding, monthly, annual, clock=lambda: NOW)

        result = await service.run_due_reviews()

        assert result.monthly_started == []
        assert result.annual_started == []
