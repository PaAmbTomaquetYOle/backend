"""Unit tests for Dossier state machine transitions."""

from __future__ import annotations

import pytest

from app.domain.dossier.state.approved import ApprovedDossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.dossier.state.draft import DraftDossierState
from app.domain.dossier.state.generating import GeneratingDossierState
from app.domain.dossier.state.not_generated import NotGeneratedDossierState
from app.domain.dossier.state.under_review import UnderReviewDossierState
from app.domain.enums import DossierStateEnum
from app.domain.exceptions.invalid_state_transition import InvalidDossierStateTransitionError


class TestNotGeneratedDossierState:
    def test_get_state_returns_not_generated(self):
        state = NotGeneratedDossierState()
        assert state.get_state() == DossierStateEnum.NOT_GENERATED

    def test_start_generating_returns_generating(self):
        state = NotGeneratedDossierState()
        new_state = state.start_generating()
        assert new_state.get_state() == DossierStateEnum.GENERATING

    def test_cancel_returns_cancelled(self):
        state = NotGeneratedDossierState()
        new_state = state.cancel()
        assert new_state.get_state() == DossierStateEnum.CANCELLED

    def test_complete_generation_raises(self):
        state = NotGeneratedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.complete_generation()

    def test_submit_for_review_raises(self):
        state = NotGeneratedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.submit_for_review()

    def test_approve_raises(self):
        state = NotGeneratedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.approve()


class TestGeneratingDossierState:
    def test_get_state_returns_generating(self):
        state = GeneratingDossierState()
        assert state.get_state() == DossierStateEnum.GENERATING

    def test_complete_generation_returns_draft(self):
        state = GeneratingDossierState()
        new_state = state.complete_generation()
        assert new_state.get_state() == DossierStateEnum.DRAFT

    def test_cancel_returns_cancelled(self):
        state = GeneratingDossierState()
        new_state = state.cancel()
        assert new_state.get_state() == DossierStateEnum.CANCELLED

    def test_start_generating_raises(self):
        state = GeneratingDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.start_generating()

    def test_submit_for_review_raises(self):
        state = GeneratingDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.submit_for_review()

    def test_approve_raises(self):
        state = GeneratingDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.approve()


class TestDraftDossierState:
    def test_get_state_returns_draft(self):
        state = DraftDossierState()
        assert state.get_state() == DossierStateEnum.DRAFT

    def test_submit_for_review_returns_under_review(self):
        state = DraftDossierState()
        new_state = state.submit_for_review()
        assert new_state.get_state() == DossierStateEnum.UNDER_REVIEW

    def test_cancel_returns_cancelled(self):
        state = DraftDossierState()
        new_state = state.cancel()
        assert new_state.get_state() == DossierStateEnum.CANCELLED

    def test_start_generating_raises(self):
        state = DraftDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.start_generating()

    def test_complete_generation_raises(self):
        state = DraftDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.complete_generation()

    def test_approve_raises(self):
        state = DraftDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.approve()


class TestUnderReviewDossierState:
    def test_get_state_returns_under_review(self):
        state = UnderReviewDossierState()
        assert state.get_state() == DossierStateEnum.UNDER_REVIEW

    def test_approve_returns_approved(self):
        state = UnderReviewDossierState()
        new_state = state.approve()
        assert new_state.get_state() == DossierStateEnum.APPROVED

    def test_cancel_returns_cancelled(self):
        state = UnderReviewDossierState()
        new_state = state.cancel()
        assert new_state.get_state() == DossierStateEnum.CANCELLED

    def test_start_generating_raises(self):
        state = UnderReviewDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.start_generating()

    def test_complete_generation_raises(self):
        state = UnderReviewDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.complete_generation()

    def test_submit_for_review_raises(self):
        state = UnderReviewDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.submit_for_review()


class TestApprovedDossierState:
    def test_get_state_returns_approved(self):
        state = ApprovedDossierState()
        assert state.get_state() == DossierStateEnum.APPROVED

    def test_start_generating_raises(self):
        state = ApprovedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.start_generating()

    def test_complete_generation_raises(self):
        state = ApprovedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.complete_generation()

    def test_submit_for_review_raises(self):
        state = ApprovedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.submit_for_review()

    def test_approve_raises(self):
        state = ApprovedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.approve()

    def test_cancel_raises(self):
        state = ApprovedDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.cancel()


class TestCancelledDossierState:
    def test_get_state_returns_cancelled(self):
        state = CancelledDossierState()
        assert state.get_state() == DossierStateEnum.CANCELLED

    def test_start_generating_raises(self):
        state = CancelledDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.start_generating()

    def test_complete_generation_raises(self):
        state = CancelledDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.complete_generation()

    def test_submit_for_review_raises(self):
        state = CancelledDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.submit_for_review()

    def test_approve_raises(self):
        state = CancelledDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.approve()

    def test_cancel_raises(self):
        state = CancelledDossierState()
        with pytest.raises(InvalidDossierStateTransitionError):
            state.cancel()
