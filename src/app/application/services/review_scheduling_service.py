"""Concrete implementation of the periodic review scheduling use case (BE-24)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime

from app.application.service_interfaces.annual_review_facade_interface import (
    IAnnualReviewServiceFacade,
)
from app.application.service_interfaces.monthly_review_facade_interface import (
    IMonthlyReviewServiceFacade,
)
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.service_interfaces.review_scheduling_service_interface import (
    IReviewSchedulingService,
    ReviewSchedulingResult,
)
from app.domain import AnnualReviewProcessStateEnum, MonthlyReviewProcessStateEnum
from app.domain.enums import OffboardingProcessStateEnum
from app.domain.review_scheduling import EmployeeReviewSnapshot, ReviewSchedulingPolicy

_ANNUAL_ACTIVE_STATES = (
    AnnualReviewProcessStateEnum.NOT_STARTED,
    AnnualReviewProcessStateEnum.IN_PROGRESS,
    AnnualReviewProcessStateEnum.PENDING_REVISION,
)
_MONTHLY_ACTIVE_STATES = (
    MonthlyReviewProcessStateEnum.NOT_STARTED,
    MonthlyReviewProcessStateEnum.IN_PROGRESS,
)


class _SnapshotBuilder:
    """Mutable accumulator for one employee's EmployeeReviewSnapshot, built by
    scanning every process (of any type) that mentions them."""

    def __init__(self, employee_id, manager_id, employee_name, manager_name, created_at) -> None:
        self.employee_id = employee_id
        self.manager_id = manager_id
        self.employee_name = employee_name
        self.manager_name = manager_name
        self.joined_at = created_at
        self.latest_seen_at = created_at
        self.has_left = False
        self.has_active_monthly_review = False
        self.has_active_annual_review = False
        self.last_monthly_review_at: datetime | None = None
        self.last_annual_review_at: datetime | None = None

    def observe(self, manager_id, employee_name, manager_name, created_at) -> None:
        self.joined_at = min(self.joined_at, created_at)
        if created_at >= self.latest_seen_at:
            self.latest_seen_at = created_at
            self.manager_id = manager_id
            self.employee_name = employee_name
            self.manager_name = manager_name

    def finalize(self) -> EmployeeReviewSnapshot:
        return EmployeeReviewSnapshot(
            employee_id=self.employee_id,
            manager_id=self.manager_id,
            employee_name=self.employee_name,
            manager_name=self.manager_name,
            joined_at=self.joined_at,
            has_left=self.has_left,
            has_active_monthly_review=self.has_active_monthly_review,
            has_active_annual_review=self.has_active_annual_review,
            last_monthly_review_at=self.last_monthly_review_at,
            last_annual_review_at=self.last_annual_review_at,
        )


def _get_or_create(
    builders: dict[str, _SnapshotBuilder], process
) -> _SnapshotBuilder:
    key = process.employee_id.get_id()
    builder = builders.get(key)
    if builder is None:
        builder = _SnapshotBuilder(
            process.employee_id,
            process.manager_id,
            process.employee_name,
            process.manager_name,
            process.created_at,
        )
        builders[key] = builder
    else:
        builder.observe(
            process.manager_id, process.employee_name, process.manager_name, process.created_at
        )
    return builder


def _build_snapshots(
    offboarding_processes: Iterable,
    monthly_processes: Iterable,
    annual_processes: Iterable,
) -> dict[str, EmployeeReviewSnapshot]:
    builders: dict[str, _SnapshotBuilder] = {}

    for process in offboarding_processes:
        builder = _get_or_create(builders, process)
        if process.state_value == OffboardingProcessStateEnum.FINISHED:
            builder.has_left = True

    for process in monthly_processes:
        builder = _get_or_create(builders, process)
        if process.state_value in _MONTHLY_ACTIVE_STATES:
            builder.has_active_monthly_review = True
        if process.state_value == MonthlyReviewProcessStateEnum.FINISHED:
            previous = builder.last_monthly_review_at
            if previous is None or process.created_at > previous:
                builder.last_monthly_review_at = process.created_at

    for process in annual_processes:
        builder = _get_or_create(builders, process)
        if process.state_value in _ANNUAL_ACTIVE_STATES:
            builder.has_active_annual_review = True
        if process.state_value == AnnualReviewProcessStateEnum.FINISHED:
            previous = builder.last_annual_review_at
            if previous is None or process.created_at > previous:
                builder.last_annual_review_at = process.created_at

    return {key: builder.finalize() for key, builder in builders.items()}


class ReviewSchedulingService(IReviewSchedulingService):
    """Sweeps every known employee/volunteer and starts a MonthlyReviewProcess
    or AnnualReviewProcess for anyone due, per ReviewSchedulingPolicy.

    Runs on a recurring schedule (infrastructure/scheduling), not in reaction
    to any inbound event. Reuses the same facades the Kafka handlers use, so
    an automatically-started review publishes the exact same
    MonthlyReviewStateChanged/AnnualReviewStateChanged events defined in
    BE-23, as if it had come from a manual trigger.
    """

    def __init__(
        self,
        offboarding_facade: IOffboardingServiceFacade,
        monthly_review_facade: IMonthlyReviewServiceFacade,
        annual_review_facade: IAnnualReviewServiceFacade,
        policy: ReviewSchedulingPolicy | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._offboarding_facade = offboarding_facade
        self._monthly_review_facade = monthly_review_facade
        self._annual_review_facade = annual_review_facade
        self._policy = policy or ReviewSchedulingPolicy()
        self._clock = clock

    async def run_due_reviews(self) -> ReviewSchedulingResult:
        offboarding_processes = await self._offboarding_facade.list_offboardings()
        monthly_processes = await self._monthly_review_facade.list_reviews()
        annual_processes = await self._annual_review_facade.list_reviews()
        snapshots = _build_snapshots(offboarding_processes, monthly_processes, annual_processes)

        now = self._clock()
        monthly_started = []
        annual_started = []

        for snapshot in snapshots.values():
            if self._policy.is_due_for_monthly_review(snapshot, now):
                process = await self._monthly_review_facade.create_review(
                    employee_id=snapshot.employee_id,
                    manager_id=snapshot.manager_id,
                    employee_name=snapshot.employee_name,
                    manager_name=snapshot.manager_name,
                )
                await self._monthly_review_facade.start_review(process.process_id)
                monthly_started.append(process.process_id)

            if self._policy.is_due_for_annual_review(snapshot, now):
                process = await self._annual_review_facade.create_review(
                    employee_id=snapshot.employee_id,
                    manager_id=snapshot.manager_id,
                    employee_name=snapshot.employee_name,
                    manager_name=snapshot.manager_name,
                )
                await self._annual_review_facade.start_review(process.process_id)
                annual_started.append(process.process_id)

        return ReviewSchedulingResult(
            monthly_started=monthly_started, annual_started=annual_started
        )
