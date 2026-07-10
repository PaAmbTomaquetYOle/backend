"""SQLModel-backed repository for SOPs."""

from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, col, delete, select

from app.application.ports.sop import ISopRepository
from app.domain.sops.id import AuthorId, ChannelId, SopId
from app.domain.sops.sop import Sop
from app.infrastructure.persistence.models.sop import SopModel
from app.infrastructure.persistence.models.tag import SopTagLink, TagModel


class SopRepository(ISopRepository):
    """SQLModel-backed implementation of ISopRepository.

    Text search uses Postgres full-text search (to_tsvector/plainto_tsquery)
    when running against Postgres. Against SQLite (used by the test suite,
    which has no to_tsvector support) it falls back to a case-insensitive
    substring match, so the same repository code is exercised in both cases.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    def save(self, sop: Sop) -> None:
        """Persist a SOP (insert or update), syncing its tags."""
        model = SopModel(
            id=sop.sop_id.get_id(),
            content=sop.content,
            author=sop.author.get_id(),
            origin_channel=sop.origin_channel.get_id(),
            version=sop.version,
            created_at=sop.created_at,
            updated_at=sop.updated_at,
            deleted_at=sop.deleted_at,
        )
        self._session.merge(model)
        self._session.flush()
        self._sync_tags(sop.sop_id.get_id(), sop.tags)
        self._session.commit()

    def _sync_tags(self, sop_id, tags: list[str]) -> None:
        """Replace the tag links for a SOP with the given tag names.

        Creates any tags that don't already exist yet (by name).
        """
        self._session.exec(delete(SopTagLink).where(col(SopTagLink.sop_id) == sop_id))
        for name in tags:
            tag = self._session.exec(
                select(TagModel).where(col(TagModel.name) == name)
            ).first()
            if tag is None:
                tag = TagModel(name=name)
                self._session.add(tag)
                self._session.flush()
            self._session.add(SopTagLink(sop_id=sop_id, tag_id=tag.id))
        self._session.flush()

    def find_by_id(self, sop_id: SopId) -> Sop | None:
        """Return the non-deleted SOP with the given ID, or None if not found."""
        model = self._session.get(SopModel, sop_id.get_id())
        if model is None or model.deleted_at is not None:
            return None
        return self._to_domain(model)

    def search(
        self,
        text: str | None,
        tags: list[str] | None,
        page: int,
        size: int,
    ) -> tuple[list[Sop], int]:
        """Search non-deleted SOPs by full-text query and/or tags (match-all)."""
        stmt = select(SopModel).where(col(SopModel.deleted_at).is_(None))

        if text:
            stmt = stmt.where(self._text_filter(text))

        if tags:
            stmt = (
                stmt.join(SopTagLink, col(SopTagLink.sop_id) == col(SopModel.id))
                .join(TagModel, col(TagModel.id) == col(SopTagLink.tag_id))
                .where(col(TagModel.name).in_(tags))
                .group_by(col(SopModel.id))
                .having(func.count(func.distinct(TagModel.name)) == len(tags))
            )

        total = len(self._session.exec(stmt).all())
        page_stmt = stmt.offset((page - 1) * size).limit(size)
        rows = self._session.exec(page_stmt).all()
        return [self._to_domain(model) for model in rows], total

    def _text_filter(self, text: str):
        """Build the text-matching predicate for the active dialect."""
        dialect = self._session.get_bind().dialect.name
        if dialect == "postgresql":
            return func.to_tsvector("english", col(SopModel.content)).op("@@")(
                func.plainto_tsquery("english", text)
            )
        return col(SopModel.content).ilike(f"%{text}%")

    def soft_delete(self, sop_id: SopId) -> None:
        """Mark the SOP with the given ID as deleted (no-op if not found)."""
        model = self._session.get(SopModel, sop_id.get_id())
        if model is None:
            return
        sop = self._to_domain(model)
        sop.mark_deleted()
        self.save(sop)

    def _to_domain(self, model: SopModel) -> Sop:
        """Reconstruct a domain Sop from its persistence model, including tags."""
        tag_rows = self._session.exec(
            select(TagModel.name)
            .join(SopTagLink, col(SopTagLink.tag_id) == col(TagModel.id))
            .where(col(SopTagLink.sop_id) == model.id)
        ).all()
        return Sop(
            sop_id=SopId(model.id),
            content=model.content,
            author=AuthorId(model.author),
            tags=list(tag_rows),
            origin_channel=ChannelId(model.origin_channel),
            created_at=model.created_at,
            version=model.version,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
