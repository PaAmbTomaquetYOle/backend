"""Unit tests for cancel() on OffboardingProcess states and entity."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.enums import OffboardingProcessStateEnum
from app.domain.exceptions.invalid_state_transition import (
    InvalidOffboardingProcessStateTransitionError,
)
from app.domain.offboarding.id import (
    DossierId,
    EmployeeId,
    InterviewId,
    ManagerId,
    OffboardingProcessId,
)
from app.domain.offboarding.process import OffboardingProcess
from app.domain.offboarding.state.cancelled import CancelledState
from app.domain.offboarding.state.finished import FinishedState
from app.domain.offboarding.state.in_progress import InProgressState
from app.domain.offboarding.state.not_started import NotStartedState
from app.domain.offboarding.state.pending_revision import PendingRevisionState

DT = datetime(2024, 1, 1, 12, 0, 0)


def make_process(state=None, interview_id=None, dossier_id=None) -> OffboardingProcess:
    return OffboardingProcess(
        process_id=OffboardingProcessId(),
        state=state or NotStartedState(),
        employee_id=EmployeeId(),
        manager_id=ManagerId(),
        created_at=DT,
        interview_id=interview_id,
        dossier_id=dossier_id,
    )


class TestCancelOnStates:
    def test_not_started_cancel_returns_cancelled(self):
        state = NotStartedState()
        new_state = state.cancel()
        assert new_state.get_state() == OffboardingProcessStateEnum.CANCELLED

    def test_in_progress_cancel_returns_cancelled(self):
        state = InProgressState()
        new_state = state.cancel()
        assert new_state.get_state() == OffboardingProcessStateEnum.CANCELLED

    def test_pending_revision_cancel_returns_cancelled(self):
        state = PendingRevisionState()
        new_state = state.cancel()
        assert new_state.get_state() == OffboardingProcessStateEnum.CANCELLED

    def test_finished_cancel_raises(self):
        state = FinishedState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.cancel()

    def test_cancelled_cancel_raises(self):
        state = CancelledState()
        with pytest.raises(InvalidOffboardingProcessStateTransitionError):
            state.cancel()


class TestOffboardingProcessCancel:
    def test_cancel_from_not_started(self):
        process = make_process(state=NotStartedState())
        process.cancel()
        assert process.state.get_state() == OffboardingProcessStateEnum.CANCELLED

    def test_cancel_from_in_progress(self):
        process = make_process(state=InProgressState())
        process.cancel()
        assert process.state.get_state() == OffboardingProcessStateEnum.CANCELLED


class TestOffboardingProcessProperties:
    def test_interview_id_property_returns_set_value(self):
        interview_id = InterviewId()
        process = make_process(interview_id=interview_id)
        assert process.interview_id is interview_id

    def test_dossier_id_property_returns_set_value(self):
        dossier_id = DossierId()
        process = make_process(dossier_id=dossier_id)
        assert process.dossier_id is dossier_id

