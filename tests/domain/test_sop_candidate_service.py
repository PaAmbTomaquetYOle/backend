"""Unit tests for SopCandidateService using a fake in-memory repository."""

from __future__ import annotations

import pytest

from app.application.services.sop_candidate_service import SopCandidateService
from app.domain.exceptions.sops import (
    InvalidSopCandidateTransitionError,
    SopCandidateNotFoundError,
)
from app.domain.sops.candidate import SopCandidate
from app.domain.sops.id import AuthorId, ChannelId


class FakeSopCandidateRepository:
    def __init__(self):
        self._by_key: dict[tuple[str, str], SopCandidate] = {}

    async def save(self, candidate: SopCandidate) -> None:
        self._by_key[(candidate.channel_id.get_id(), candidate.message_ts)] = candidate

    async def find_by_channel_and_ts(self, channel_id: ChannelId, message_ts: str):
        return self._by_key.get((channel_id.get_id(), message_ts))

    async def find_pending(self):
        return [c for c in self._by_key.values() if c.is_pending]


@pytest.fixture(name="repo")
def repo_fixture():
    return FakeSopCandidateRepository()


@pytest.fixture(name="service")
def service_fixture(repo):
    return SopCandidateService(repo)


@pytest.mark.anyio
class TestRecordOffer:
    async def test_creates_a_new_pending_candidate(self, service):
        candidate = await service.record_offer(
            ChannelId("C1"), AuthorId("U1"), "1720000000.0001", "Some tip"
        )
        assert candidate.is_pending
        assert candidate.content == "Some tip"

    async def test_is_idempotent_on_redelivery(self, service):
        first = await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-1", "content")
        second = await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-1", "content")
        assert first.candidate_id.get_id() == second.candidate_id.get_id()


@pytest.mark.anyio
class TestRecordDecision:
    async def test_accepted_marks_the_candidate_accepted(self, service):
        await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-1", "content")
        decided = await service.record_decision(ChannelId("C1"), "ts-1", accepted=True)
        assert decided.status.value == "accepted"

    async def test_rejected_marks_the_candidate_rejected(self, service):
        await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-1", "content")
        decided = await service.record_decision(ChannelId("C1"), "ts-1", accepted=False)
        assert decided.status.value == "rejected"

    async def test_raises_when_no_candidate_exists(self, service):
        with pytest.raises(SopCandidateNotFoundError):
            await service.record_decision(ChannelId("C-unknown"), "ts-x", accepted=True)

    async def test_raises_when_already_decided(self, service):
        await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-1", "content")
        await service.record_decision(ChannelId("C1"), "ts-1", accepted=True)
        with pytest.raises(InvalidSopCandidateTransitionError):
            await service.record_decision(ChannelId("C1"), "ts-1", accepted=False)


@pytest.mark.anyio
class TestListPending:
    async def test_returns_only_pending_candidates(self, service):
        await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-1", "a")
        await service.record_offer(ChannelId("C1"), AuthorId("U1"), "ts-2", "b")
        await service.record_decision(ChannelId("C1"), "ts-2", accepted=True)

        pending = await service.list_pending()

        assert {c.message_ts for c in pending} == {"ts-1"}
