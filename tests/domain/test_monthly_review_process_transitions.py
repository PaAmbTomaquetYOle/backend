"""Unit tests for start(), complete(), and cancel() on MonthlyReviewProcess states and entity."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.enums import MonthlyReviewProcessStateEnum
from app.domain.exceptions.invalid_state_transition import (
    InvalidMonthlyReviewProcessStateTransitionError,
)
from app.domain.monthly_review.id import MonthlyReviewProcessId
from app.domain.monthly_review.process import MonthlyReviewProcess
from app.domain.monthly_review.state.cancelled import CancelledState
from app.domain.monthly_review.state.finished import FinishedState
from app.domain.monthly_review.state.in_progress import InProgressState
from app.domain.monthly_review.state.not_started import NotStartedState
from app.domain.offboarding.id import EmployeeId, ManagerId

DT = datetime(2024, 1, 1, 12, 0, 0)


def make_process(state=None) -> MonthlyReviewProcess:
    return MonthlyReviewProcess(
        process_id=MonthlyReviewProcessId(),
        state=state or NotStartedState(),
        employee_id=EmployeeId(),
        manager_id=ManagerId(),
        created_at=DT,
    )


class TestStartOnStates:
    def test_not_started_start_returns_in_progress(self):
        state = NotStartedState()
        new_state = state.start()
        assert new_state.get_state() == MonthlyReviewProcessStateEnum.IN_PROGRESS

    def test_in_progress_start_raises(self):
        state = InProgressState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.start()

    def test_finished_start_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.start()

    def test_cancelled_start_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.start()


class TestCompleteOnStates:
    def test_in_progress_complete_returns_finished(self):
        state = InProgressState()
        new_state = state.complete()
        assert new_state.get_state() == MonthlyReviewProcessStateEnum.FINISHED

    def test_not_started_complete_raises(self):
        state = NotStartedState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.complete()

    def test_finished_complete_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.complete()

    def test_cancelled_complete_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.complete()


class TestCancelOnStates:
    def test_not_started_cancel_returns_cancelled(self):
        state = NotStartedState()
        new_state = state.cancel()
        assert new_state.get_state() == MonthlyReviewProcessStateEnum.CANCELLED

    def test_in_progress_cancel_returns_cancelled(self):
        state = InProgressState()
        new_state = state.cancel()
        assert new_state.get_state() == MonthlyReviewProcessStateEnum.CANCELLED

    def test_finished_cancel_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.cancel()

    def test_cancelled_cancel_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            state.cancel()


class TestMonthlyReviewProcessFullLifecycle:
    def test_full_happy_path(self):
        process = make_process(state=NotStartedState())
        process.start()
        process.complete()
        assert process.state.get_state() == MonthlyReviewProcessStateEnum.FINISHED

    def test_cancel_from_in_progress(self):
        process = make_process(state=InProgressState())
        process.cancel()
        assert process.state.get_state() == MonthlyReviewProcessStateEnum.CANCELLED

    def test_complete_from_not_started_raises(self):
        process = make_process(state=NotStartedState())
        with pytest.raises(InvalidMonthlyReviewProcessStateTransitionError):
            process.complete()
