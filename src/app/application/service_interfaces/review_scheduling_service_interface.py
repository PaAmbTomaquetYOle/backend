"""Abstract contract for the periodic review scheduling use case (BE-24)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain import AnnualReviewProcessId, MonthlyReviewProcessId


@dataclass(frozen=True)
class ReviewSchedulingResult:
    """Summary of one scheduling sweep, for logging and testing."""

    monthly_started: list[MonthlyReviewProcessId]
    annual_started: list[AnnualReviewProcessId]


class IReviewSchedulingService(ABC):
    """Interface for the use case that creates due periodic review processes.

    Implemented by ReviewSchedulingService, invoked on a recurring schedule
    (see infrastructure/scheduling) rather than by an inbound Kafka event or
    HTTP request — there is no external trigger for these processes.
    """

    @abstractmethod
    async def run_due_reviews(self) -> ReviewSchedulingResult:
        """Create and start a MonthlyReviewProcess/AnnualReviewProcess for every
        employee who is currently due for one, per ReviewSchedulingPolicy.

        Idempotent per employee/review-type: an employee already covered by an
        active review process of that type is skipped.

        Returns:
            ReviewSchedulingResult listing the process IDs that were started.
        """
