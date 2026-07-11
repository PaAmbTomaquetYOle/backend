"""Domain policy deciding which employees are due for a periodic knowledge-retention review.

BE-24: this backend has no separate employee/volunteer roster — ``employee_id``
is just an opaque Slack user ID recorded on whichever processes that person
has been part of. So "who is an active employee/volunteer" and "when did they
join" are both derived from the processes we already know about, rather than
from an external HR system this project doesn't have.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.offboarding.id import EmployeeId, ManagerId


@dataclass(frozen=True)
class EmployeeReviewSnapshot:
    """Everything the scheduling policy needs to know about one employee.

    Built by scanning every known process (offboarding, monthly review,
    annual review) for a given employee_id — see ReviewSchedulingService.
    """

    employee_id: EmployeeId
    manager_id: ManagerId
    employee_name: str | None
    manager_name: str | None
    joined_at: datetime
    has_left: bool
    has_active_monthly_review: bool
    has_active_annual_review: bool
    last_monthly_review_at: datetime | None
    last_annual_review_at: datetime | None


class ReviewSchedulingPolicy:
    """Decides whether an employee is due for a monthly or annual review today.

    Eligibility criteria (BE-24):
    - The employee must not have left (no FINISHED OffboardingProcess) — once
      someone has actually offboarded, periodic reviews stop.
    - The employee must not already have an active (NOT_STARTED/IN_PROGRESS)
      review process of that type — never double-schedule.
    - The interval since their last review of that type (or since they first
      appeared in the system, if they've never had one) must have elapsed.
    """

    MONTHLY_INTERVAL = timedelta(days=30)
    ANNUAL_INTERVAL = timedelta(days=365)

    def is_due_for_monthly_review(self, snapshot: EmployeeReviewSnapshot, now: datetime) -> bool:
        """Whether this employee should get a new MonthlyReviewProcess today."""
        if snapshot.has_left or snapshot.has_active_monthly_review:
            return False
        anchor = snapshot.last_monthly_review_at or snapshot.joined_at
        return now - anchor >= self.MONTHLY_INTERVAL

    def is_due_for_annual_review(self, snapshot: EmployeeReviewSnapshot, now: datetime) -> bool:
        """Whether this employee should get a new AnnualReviewProcess today."""
        if snapshot.has_left or snapshot.has_active_annual_review:
            return False
        anchor = snapshot.last_annual_review_at or snapshot.joined_at
        return now - anchor >= self.ANNUAL_INTERVAL
