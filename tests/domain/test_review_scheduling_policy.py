"""Unit tests for ReviewSchedulingPolicy (BE-24)."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.offboarding.id import EmployeeId, ManagerId
from app.domain.review_scheduling import EmployeeReviewSnapshot, ReviewSchedulingPolicy

NOW = datetime(2026, 7, 11, 12, 0, 0)


def make_snapshot(
    joined_at: datetime = NOW - timedelta(days=1000),
    has_left: bool = False,
    has_active_monthly_review: bool = False,
    has_active_annual_review: bool = False,
    last_monthly_review_at: datetime | None = None,
    last_annual_review_at: datetime | None = None,
) -> EmployeeReviewSnapshot:
    return EmployeeReviewSnapshot(
        employee_id=EmployeeId("U1"),
        manager_id=ManagerId("U2"),
        employee_name="Alice",
        manager_name="Bob",
        joined_at=joined_at,
        has_left=has_left,
        has_active_monthly_review=has_active_monthly_review,
        has_active_annual_review=has_active_annual_review,
        last_monthly_review_at=last_monthly_review_at,
        last_annual_review_at=last_annual_review_at,
    )


class TestIsDueForMonthlyReview:
    def test_due_when_never_reviewed_and_joined_over_30_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(joined_at=NOW - timedelta(days=31))
        assert policy.is_due_for_monthly_review(snapshot, NOW) is True

    def test_not_due_when_joined_less_than_30_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(joined_at=NOW - timedelta(days=10))
        assert policy.is_due_for_monthly_review(snapshot, NOW) is False

    def test_due_when_last_review_over_30_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(last_monthly_review_at=NOW - timedelta(days=31))
        assert policy.is_due_for_monthly_review(snapshot, NOW) is True

    def test_not_due_when_last_review_less_than_30_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(last_monthly_review_at=NOW - timedelta(days=5))
        assert policy.is_due_for_monthly_review(snapshot, NOW) is False

    def test_not_due_when_employee_has_left(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(joined_at=NOW - timedelta(days=1000), has_left=True)
        assert policy.is_due_for_monthly_review(snapshot, NOW) is False

    def test_not_due_when_already_has_active_monthly_review(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(
            joined_at=NOW - timedelta(days=1000), has_active_monthly_review=True
        )
        assert policy.is_due_for_monthly_review(snapshot, NOW) is False

    def test_active_annual_review_does_not_block_monthly(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(
            joined_at=NOW - timedelta(days=1000), has_active_annual_review=True
        )
        assert policy.is_due_for_monthly_review(snapshot, NOW) is True


class TestIsDueForAnnualReview:
    def test_due_when_never_reviewed_and_joined_over_365_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(joined_at=NOW - timedelta(days=366))
        assert policy.is_due_for_annual_review(snapshot, NOW) is True

    def test_not_due_when_joined_less_than_365_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(joined_at=NOW - timedelta(days=100))
        assert policy.is_due_for_annual_review(snapshot, NOW) is False

    def test_due_when_last_review_over_365_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(last_annual_review_at=NOW - timedelta(days=366))
        assert policy.is_due_for_annual_review(snapshot, NOW) is True

    def test_not_due_when_last_review_less_than_365_days_ago(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(last_annual_review_at=NOW - timedelta(days=100))
        assert policy.is_due_for_annual_review(snapshot, NOW) is False

    def test_not_due_when_employee_has_left(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(joined_at=NOW - timedelta(days=1000), has_left=True)
        assert policy.is_due_for_annual_review(snapshot, NOW) is False

    def test_not_due_when_already_has_active_annual_review(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(
            joined_at=NOW - timedelta(days=1000), has_active_annual_review=True
        )
        assert policy.is_due_for_annual_review(snapshot, NOW) is False

    def test_active_monthly_review_does_not_block_annual(self) -> None:
        policy = ReviewSchedulingPolicy()
        snapshot = make_snapshot(
            joined_at=NOW - timedelta(days=1000), has_active_monthly_review=True
        )
        assert policy.is_due_for_annual_review(snapshot, NOW) is True
