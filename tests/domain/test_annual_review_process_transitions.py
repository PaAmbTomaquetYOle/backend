"""Unit tests for start(), submit_for_review(), complete(), and cancel() on
AnnualReviewProcess states and entity."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.annual_review.id import AnnualReviewProcessId
from app.domain.annual_review.process import AnnualReviewProcess
from app.domain.annual_review.state.cancelled import CancelledState
from app.domain.annual_review.state.finished import FinishedState
from app.domain.annual_review.state.in_progress import InProgressState
from app.domain.annual_review.state.not_started import NotStartedState
from app.domain.annual_review.state.pending_revision import PendingRevisionState
from app.domain.enums import AnnualReviewProcessStateEnum
from app.domain.exceptions.invalid_state_transition import (
    InvalidAnnualReviewProcessStateTransitionError,
)
from app.domain.offboarding.id import EmployeeId, ManagerId

DT = datetime(2024, 1, 1, 12, 0, 0)


def make_process(state=None) -> AnnualReviewProcess:
    return AnnualReviewProcess(
        process_id=AnnualReviewProcessId(),
        state=state or NotStartedState(),
        employee_id=EmployeeId(),
        manager_id=ManagerId(),
        created_at=DT,
    )


class TestStartOnStates:
    def test_not_started_start_returns_in_progress(self):
        state = NotStartedState()
        new_state = state.start()
        assert new_state.get_state() == AnnualReviewProcessStateEnum.IN_PROGRESS

    def test_in_progress_start_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            InProgressState().start()

    def test_pending_revision_start_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            PendingRevisionState().start()

    def test_finished_start_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            FinishedState().start()

    def test_cancelled_start_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            CancelledState().start()


class TestSubmitForReviewOnStates:
    def test_in_progress_submit_for_review_returns_pending_revision(self):
        new_state = InProgressState().submit_for_review()
        assert new_state.get_state() == AnnualReviewProcessStateEnum.PENDING_REVISION

    def test_not_started_submit_for_review_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            NotStartedState().submit_for_review()

    def test_finished_submit_for_review_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            FinishedState().submit_for_review()


class TestCompleteOnStates:
    def test_pending_revision_complete_returns_finished(self):
        new_state = PendingRevisionState().complete()
        assert new_state.get_state() == AnnualReviewProcessStateEnum.FINISHED

    def test_in_progress_complete_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            InProgressState().complete()

    def test_not_started_complete_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            NotStartedState().complete()


class TestCancelOnStates:
    def test_not_started_cancel_returns_cancelled(self):
        assert NotStartedState().cancel().get_state() == AnnualReviewProcessStateEnum.CANCELLED

    def test_in_progress_cancel_returns_cancelled(self):
        assert InProgressState().cancel().get_state() == AnnualReviewProcessStateEnum.CANCELLED

    def test_pending_revision_cancel_returns_cancelled(self):
        assert PendingRevisionState().cancel().get_state() == AnnualReviewProcessStateEnum.CANCELLED

    def test_finished_cancel_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            FinishedState().cancel()

    def test_cancelled_cancel_raises(self):
        with pytest.raises(InvalidAnnualReviewProcessStateTransitionError):
            CancelledState().cancel()


class TestAnnualReviewProcessFullLifecycle:
    def test_full_happy_path(self):
        process = make_process(state=NotStartedState())
        process.start()
        process.submit_for_review()
        process.complete()
        assert process.state.get_state() == AnnualReviewProcessStateEnum.FINISHED

    def test_cancel_from_in_progress(self):
        process = make_process(state=InProgressState())
        process.cancel()
        assert process.state.get_state() == AnnualReviewProcessStateEnum.CANCELLED
