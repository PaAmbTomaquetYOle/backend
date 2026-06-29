"""Unit tests for start(), submit_for_review(), and complete() on OffboardingProcess states and entity."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.exceptions.invalid_state_transition import (
    InvalidOffboardingProcessStateTransitionError,
)
from app.domain.offboarding.id import EmployeeId, ManagerId, OffboardingProcessId
from app.domain.offboarding.process import OffboardingProcess
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.finished import FinishedState
from app.domain.offboarding.state.in_progress import InProgressState
from app.domain.offboarding.state.not_started import NotStartedState
from app.domain.offboarding.state.pending_revision import PendingRevisionState

DT = datetime(2024, 1, 1, 12, 0, 0)


def make_process(state=None) -> OffboardingProcess:
    return OffboardingProcess(
        process_id=OffboardingProcessId(),
        state=state or NotStartedState(),
        employee_id=EmployeeId(),
        manager_id=ManagerId(),
        created_at=DT,
    )


class TestStartOnStates:
    def test_not_started_start_returns_in_progress(self):
        state = NotStartedState()
        new_state = state.start()
        assert new_state.get_state() == OffboardingProcessStateEnum.IN_PROGRESS

    def test_in_progress_start_raises(self):
        state = InProgressState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.start()

    def test_pending_revision_start_raises(self):
        state = PendingRevisionState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.start()

    def test_finished_start_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.start()

    def test_cancelled_start_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.start()


class TestSubmitForReviewOnStates:
    def test_in_progress_submit_for_review_returns_pending_revision(self):
        state = InProgressState()
        new_state = state.submit_for_review()
        assert new_state.get_state() == OffboardingProcessStateEnum.PENDING_REVISION

    def test_not_started_submit_for_review_raises(self):
        state = NotStartedState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.submit_for_review()

    def test_pending_revision_submit_for_review_raises(self):
        state = PendingRevisionState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.submit_for_review()

    def test_finished_submit_for_review_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.submit_for_review()

    def test_cancelled_submit_for_review_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.submit_for_review()


class TestCompleteOnStates:
    def test_pending_revision_complete_returns_finished(self):
        state = PendingRevisionState()
        new_state = state.complete()
        assert new_state.get_state() == OffboardingProcessStateEnum.FINISHED

    def test_not_started_complete_raises(self):
        state = NotStartedState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.complete()

    def test_in_progress_complete_raises(self):
        state = InProgressState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.complete()

    def test_finished_complete_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.complete()

    def test_cancelled_complete_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.complete()


class TestOffboardingProcessStart:
    def test_start_transitions_to_in_progress(self):
        process = make_process(state=NotStartedState())
        process.start()
        assert process.state.get_state() == OffboardingProcessStateEnum.IN_PROGRESS

    def test_start_from_in_progress_raises(self):
        process = make_process(state=InProgressState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.start()

    def test_start_from_cancelled_raises(self):
        process = make_process(state=CancelledState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.start()


class TestOffboardingProcessSubmitForReview:
    def test_submit_for_review_transitions_to_pending_revision(self):
        process = make_process(state=InProgressState())
        process.submit_for_review()
        assert process.state.get_state() == OffboardingProcessStateEnum.PENDING_REVISION

    def test_submit_for_review_from_not_started_raises(self):
        process = make_process(state=NotStartedState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.submit_for_review()

    def test_submit_for_review_from_finished_raises(self):
        process = make_process(state=FinishedState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.submit_for_review()


class TestOffboardingProcessComplete:
    def test_complete_transitions_to_finished(self):
        process = make_process(state=PendingRevisionState())
        process.complete()
        assert process.state.get_state() == OffboardingProcessStateEnum.FINISHED

    def test_complete_from_in_progress_raises(self):
        process = make_process(state=InProgressState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.complete()

    def test_complete_from_not_started_raises(self):
        process = make_process(state=NotStartedState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.complete()

    def test_complete_from_cancelled_raises(self):
        process = make_process(state=CancelledState())
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            process.complete()


class TestOffboardingProcessFullLifecycle:
    def test_full_happy_path(self):
        process = make_process(state=NotStartedState())
        process.start()
        process.submit_for_review()
        process.complete()
        assert process.state.get_state() == OffboardingProcessStateEnum.FINISHED
