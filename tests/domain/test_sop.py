"""Unit tests for the Sop aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop


def make_sop(content: str = "How to rotate secrets", tags: list[str] | None = None) -> Sop:
    return Sop(
        sop_id=SopId(),
        content=content,
        author=AuthorId("U123"),
        tags=tags or ["security", "onboarding"],
        origin_channel=ChannelId("C456"),
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


class TestCreation:
    def test_starts_at_version_1(self) -> None:
        sop = make_sop()
        assert sop.version == 1

    def test_updated_at_defaults_to_created_at(self) -> None:
        sop = make_sop()
        assert sop.updated_at == sop.created_at

    def test_not_deleted_by_default(self) -> None:
        sop = make_sop()
        assert sop.is_deleted is False
        assert sop.deleted_at is None

    def test_tags_are_copied_not_aliased(self) -> None:
        tags = ["a", "b"]
        sop = make_sop(tags=tags)
        tags.append("c")
        assert sop.tags == ["a", "b"]


class TestRevise:
    def test_revise_content_increments_version(self) -> None:
        sop = make_sop()
        sop.revise(content="Updated content")
        assert sop.content == "Updated content"
        assert sop.version == 2

    def test_revise_tags_only_leaves_content_unchanged(self) -> None:
        sop = make_sop(content="original")
        sop.revise(tags=["new-tag"])
        assert sop.content == "original"
        assert sop.tags == ["new-tag"]
        assert sop.version == 2

    def test_revise_updates_updated_at(self) -> None:
        sop = make_sop()
        before = sop.updated_at
        sop.revise(content="x")
        assert sop.updated_at >= before

    def test_multiple_revisions_accumulate_version(self) -> None:
        sop = make_sop()
        sop.revise(content="v2")
        sop.revise(content="v3")
        assert sop.version == 3


class TestMarkDeleted:
    def test_mark_deleted_sets_deleted_at(self) -> None:
        sop = make_sop()
        sop.mark_deleted()
        assert sop.is_deleted is True
        assert sop.deleted_at is not None
