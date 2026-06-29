"""Unit tests for Interview state machine transitions."""

from __future__ import annotations

import pytest

from app.domain.enums import InterviewStateEnum
from app.domain.exceptions.invalid_state_transition import InvalidInterviewStateTransitionError
from app.domain.interview.state.cancelled import CancelledInterviewState
from app.domain.interview.state.completed import CompletedInterviewState
from app.domain.interview.state.in_progress import InProgressInterviewState
from app.domain.interview.state.scheduled import ScheduledInterviewState


class TestScheduledInterviewState:
    def test_get_state_returns_scheduled(self):
        state = ScheduledInterviewState()
        assert state.get_state() == InterviewStateEnum.SCHEDULED

    def test_start_returns_in_progress(self):
        state = ScheduledInterviewState()
        new_state = state.start()
        assert new_state.get_state() == InterviewStateEnum.IN_PROGRESS

    def test_cancel_returns_cancelled(self):
        state = ScheduledInterviewState()
        new_state = state.cancel()
        assert new_state.get_state() == InterviewStateEnum.CANCELLED

    def test_complete_raises(self):
        state = ScheduledInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.complete()


class TestInProgressInterviewState:
    def test_get_state_returns_in_progress(self):
        state = InProgressInterviewState()
        assert state.get_state() == InterviewStateEnum.IN_PROGRESS

    def test_complete_returns_completed(self):
        state = InProgressInterviewState()
        new_state = state.complete()
        assert new_state.get_state() == InterviewStateEnum.COMPLETED

    def test_cancel_returns_cancelled(self):
        state = InProgressInterviewState()
        new_state = state.cancel()
        assert new_state.get_state() == InterviewStateEnum.CANCELLED

    def test_start_raises(self):
        state = InProgressInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.start()


class TestCompletedInterviewState:
    def test_get_state_returns_completed(self):
        state = CompletedInterviewState()
        assert state.get_state() == InterviewStateEnum.COMPLETED

    def test_start_raises(self):
        state = CompletedInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.start()

    def test_complete_raises(self):
        state = CompletedInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.complete()

    def test_cancel_raises(self):
        state = CompletedInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.cancel()


class TestCancelledInterviewState:
    def test_get_state_returns_cancelled(self):
        state = CancelledInterviewState()
        assert state.get_state() == InterviewStateEnum.CANCELLED

    def test_start_raises(self):
        state = CancelledInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.start()

    def test_complete_raises(self):
        state = CancelledInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.complete()

    def test_cancel_raises(self):
        state = CancelledInterviewState()
        with pytest.raises(InvalidInterviewStateTransitionError):
            state.cancel()
