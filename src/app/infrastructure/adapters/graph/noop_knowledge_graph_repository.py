"""No-op knowledge graph repository — fallback when Neo4j is unavailable."""

from __future__ import annotations

import logging

from app.application.ports.knowledge_graph import IKnowledgeGraphRepository
from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonAnalytics,
    PersonKnowledgeProfile,
    PersonNode,
    SuccessorCandidate,
    TopicNode,
)

logger = logging.getLogger(__name__)


class NoOpKnowledgeGraphRepository(IKnowledgeGraphRepository):
    """Fallback repository used when the graph database is unreachable.

    All writes are no-ops (logged) and all reads return empty results,
    following the same pattern as NoOpGraphAdapter, so the application keeps
    serving requests even when Neo4j is down.
    """

    async def upsert_person(
        self, person_id: str, name: str, department: str | None = None
    ) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning("NoOpKnowledgeGraphRepository.upsert_person called for %s", person_id)

    async def upsert_topic(self, name: str, description: str | None = None) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning("NoOpKnowledgeGraphRepository.upsert_topic called for %s", name)

    async def upsert_document(
        self,
        document_id: str,
        title: str,
        url: str | None = None,
        source: str | None = None,
    ) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning("NoOpKnowledgeGraphRepository.upsert_document called for %s", document_id)

    async def upsert_channel(self, channel_id: str, name: str) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning("NoOpKnowledgeGraphRepository.upsert_channel called for %s", channel_id)

    async def register_expertise(
        self, person_id: str, topic_name: str, weight: float = 1.0
    ) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning(
            "NoOpKnowledgeGraphRepository.register_expertise called for %s/%s",
            person_id,
            topic_name,
        )

    async def register_authorship(self, person_id: str, document_id: str) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning(
            "NoOpKnowledgeGraphRepository.register_authorship called for %s/%s",
            person_id,
            document_id,
        )

    async def register_answer(self, person_id: str, topic_name: str) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning(
            "NoOpKnowledgeGraphRepository.register_answer called for %s/%s",
            person_id,
            topic_name,
        )

    async def register_topic_mention(self, topic_name: str, channel_id: str) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning(
            "NoOpKnowledgeGraphRepository.register_topic_mention called for %s/%s",
            topic_name,
            channel_id,
        )

    async def register_activity(self, person_id: str, channel_id: str) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning(
            "NoOpKnowledgeGraphRepository.register_activity called for %s/%s",
            person_id,
            channel_id,
        )

    async def register_document_reference(self, document_id: str, topic_name: str) -> None:
        """No-op — logs a warning instead of writing."""
        logger.warning(
            "NoOpKnowledgeGraphRepository.register_document_reference called for %s/%s",
            document_id,
            topic_name,
        )

    async def find_experts_by_topic(self, topic_name: str, limit: int = 10) -> list[ExpertResult]:
        """Always returns an empty list."""
        logger.warning("NoOpKnowledgeGraphRepository.find_experts_by_topic called")
        return []

    async def find_topics_by_person(self, person_id: str) -> list[TopicNode]:
        """Always returns an empty list."""
        logger.warning("NoOpKnowledgeGraphRepository.find_topics_by_person called")
        return []

    async def find_person_knowledge_profile(
        self, person_id: str
    ) -> PersonKnowledgeProfile | None:
        """Always returns None."""
        logger.warning("NoOpKnowledgeGraphRepository.find_person_knowledge_profile called")
        return None

    async def find_related_topics(self, topic_name: str, limit: int = 10) -> list[TopicNode]:
        """Always returns an empty list."""
        logger.warning("NoOpKnowledgeGraphRepository.find_related_topics called")
        return []

    async def find_documents_by_topic(
        self, topic_name: str, limit: int = 20
    ) -> list[DocumentNode]:
        """Always returns an empty list."""
        logger.warning("NoOpKnowledgeGraphRepository.find_documents_by_topic called")
        return []

    async def find_all_topics(self, page: int = 1, size: int = 50) -> tuple[list[TopicNode], int]:
        """Always returns an empty page."""
        logger.warning("NoOpKnowledgeGraphRepository.find_all_topics called")
        return [], 0

    async def find_all_persons(
        self, page: int = 1, size: int = 50
    ) -> tuple[list[PersonNode], int]:
        """Always returns an empty page."""
        logger.warning("NoOpKnowledgeGraphRepository.find_all_persons called")
        return [], 0

    async def compute_person_analytics(self) -> list[PersonAnalytics]:
        """Always returns an empty list."""
        logger.warning("NoOpKnowledgeGraphRepository.compute_person_analytics called")
        return []

    async def find_successor_candidates(
        self, person_id: str, limit: int = 5
    ) -> list[SuccessorCandidate]:
        """Always returns an empty list."""
        logger.warning("NoOpKnowledgeGraphRepository.find_successor_candidates called")
        return []
