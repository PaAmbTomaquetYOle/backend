"""Concrete implementation of the knowledge graph service."""

import logging

from app.application.ports.event_publisher import IEventPublisher
from app.application.ports.knowledge_graph import IKnowledgeGraphRepository
from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.domain.events.knowledge_graph_events import KnowledgeGraphUpdated
from app.domain.exceptions.knowledge_graph import PersonNotFoundInGraphError
from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonKnowledgeProfile,
    PersonNode,
    TopicNode,
)

logger = logging.getLogger(__name__)

KNOWS_INTERACTION = "knows"
ANSWERED_INTERACTION = "answered"


class KnowledgeGraphService(IKnowledgeGraphService):
    """Orchestrates knowledge graph use cases: querying and populating the graph.

    Delegates all graph access to IKnowledgeGraphRepository and publishes
    KnowledgeGraphUpdated after mutations via a defensive helper, mirroring
    SopService.
    """

    def __init__(
        self,
        repo: IKnowledgeGraphRepository,
        event_publisher: IEventPublisher | None = None,
    ) -> None:
        """Set up the service with a repository and an optional event publisher.

        Args:
            repo: The repository used to read and write the knowledge graph.
            event_publisher: Optional publisher for domain events. If None,
                events are not published.
        """
        self._repo = repo
        self._event_publisher = event_publisher

    async def _publish(self, event) -> None:
        """Publish a domain event, logging a warning if publishing fails.

        Args:
            event: The domain event to publish.
        """
        if self._event_publisher is not None:
            try:
                await self._event_publisher.publish(event)
            except Exception:
                logger.warning("Failed to publish event %s", event.event_type, exc_info=True)

    async def get_experts_by_topic(self, topic: str, limit: int = 10) -> list[ExpertResult]:
        """Return the persons most associated with a topic, ranked by score."""
        return await self._repo.find_experts_by_topic(topic, limit=limit)

    async def get_person_profile(self, person_id: str) -> PersonKnowledgeProfile:
        """Return a person's full knowledge profile.

        Raises:
            PersonNotFoundInGraphError: If no person with this ID exists in the graph.
        """
        profile = await self._repo.find_person_knowledge_profile(person_id)
        if profile is None:
            raise PersonNotFoundInGraphError(person_id)
        return profile

    async def get_topics(self, page: int = 1, size: int = 50) -> tuple[list[TopicNode], int]:
        """Return a page of topics known to the graph plus the total count."""
        return await self._repo.find_all_topics(page=page, size=size)

    async def get_persons(self, page: int = 1, size: int = 50) -> tuple[list[PersonNode], int]:
        """Return a page of persons known to the graph plus the total count."""
        return await self._repo.find_all_persons(page=page, size=size)

    async def get_related_topics(self, topic: str, limit: int = 10) -> list[TopicNode]:
        """Return topics related to the given topic."""
        return await self._repo.find_related_topics(topic, limit=limit)

    async def get_documents_by_topic(self, topic: str, limit: int = 20) -> list[DocumentNode]:
        """Return documents that reference the given topic."""
        return await self._repo.find_documents_by_topic(topic, limit=limit)

    async def register_interaction(
        self,
        person_id: str,
        person_name: str,
        topic_name: str,
        interaction_type: str,
        department: str | None = None,
        topic_description: str | None = None,
    ) -> None:
        """Record that a person interacted with a topic.

        Args:
            person_id: External Slack user ID of the person.
            person_name: Display name of the person.
            topic_name: Name of the topic.
            interaction_type: Either "knows" (KNOWS_ABOUT) or "answered" (ANSWERED_ABOUT).
            department: Optional department of the person.
            topic_description: Optional description of the topic.
        """
        await self._repo.upsert_person(person_id, person_name, department=department)
        await self._repo.upsert_topic(topic_name, description=topic_description)
        if interaction_type == ANSWERED_INTERACTION:
            await self._repo.register_answer(person_id, topic_name)
        else:
            await self._repo.register_expertise(person_id, topic_name)
        await self._publish(
            KnowledgeGraphUpdated(entity_type="person", entity_id=person_id, action="interaction")
        )

    async def register_document(
        self,
        document_id: str,
        title: str,
        author_id: str,
        author_name: str,
        topics: list[str],
        url: str | None = None,
        source: str | None = None,
    ) -> None:
        """Record a document, its author, and the topics it references."""
        await self._repo.upsert_person(author_id, author_name)
        await self._repo.upsert_document(document_id, title, url=url, source=source)
        await self._repo.register_authorship(author_id, document_id)
        for topic_name in topics:
            await self._repo.upsert_topic(topic_name)
            await self._repo.register_document_reference(document_id, topic_name)
        await self._publish(
            KnowledgeGraphUpdated(entity_type="document", entity_id=document_id, action="created")
        )

    async def register_channel_activity(
        self,
        person_id: str,
        person_name: str,
        channel_id: str,
        channel_name: str,
    ) -> None:
        """Record that a person is active in a channel."""
        await self._repo.upsert_person(person_id, person_name)
        await self._repo.upsert_channel(channel_id, channel_name)
        await self._repo.register_activity(person_id, channel_id)
        await self._publish(
            KnowledgeGraphUpdated(entity_type="person", entity_id=person_id, action="activity")
        )
