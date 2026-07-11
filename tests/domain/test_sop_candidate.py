"""Unit tests for the SopCandidate aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.exceptions.sops import InvalidSopCandidateTransitionError
from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import AuthorId, ChannelId, SopCandidateId


def make_candidate(content: str = "Rotate secrets every 90 days") -> SopCandidate:
    return SopCandidate(
        candidate_id=SopCandidateId(),
        channel_id=ChannelId("C1"),
        author_id=AuthorId("U1"),
        message_ts="1720000000.000100",
        content=content,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


class TestCreation:
    def test_starts_offered_and_pending(self) -> None:
        candidate = make_candidate()
        assert candidate.status.value == "offered"
        assert candidate.is_pending is True

    def test_updated_at_defaults_to_created_at(self) -> None:
        candidate = make_candidate()
        assert candidate.updated_at == candidate.created_at


class TestMarkAccepted:
    def test_transitions_to_accepted_and_no_longer_pending(self) -> None:
        candidate = make_candidate()
        candidate.mark_accepted()
        assert candidate.status.value == "accepted"
        assert candidate.is_pending is False

    def test_raises_if_already_decided(self) -> None:
        candidate = make_candidate()
        candidate.mark_accepted()
        with pytest.raises(InvalidSopCandidateTransitionError):
            candidate.mark_accepted()


class TestMarkRejected:
    def test_transitions_to_rejected_and_no_longer_pending(self) -> None:
        candidate = make_candidate()
        candidate.mark_rejected()
        assert candidate.status.value == "rejected"
        assert candidate.is_pending is False

    def test_raises_if_already_decided(self) -> None:
        candidate = make_candidate()
        candidate.mark_rejected()
        with pytest.raises(InvalidSopCandidateTransitionError):
            candidate.mark_rejected()

    def test_accepted_candidate_cannot_then_be_rejected(self) -> None:
        candidate = make_candidate()
        candidate.mark_accepted()
        with pytest.raises(InvalidSopCandidateTransitionError):
            candidate.mark_rejected()
