"""Inbound port (service contract) for knowledge graph use cases."""

from abc import ABC, abstractmethod

from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonKnowledgeProfile,
    PersonNode,
    TopicNode,
)


class IKnowledgeGraphService(ABC):
    """Use cases exposed for querying and populating the knowledge graph."""

    # --- Read use cases (backing the REST API) ---

    @abstractmethod
    async def get_experts_by_topic(self, topic: str, limit: int = 10) -> list[ExpertResult]:
        """Return the persons most associated with a topic, ranked by score."""

    @abstractmethod
    async def get_person_profile(self, person_id: str) -> PersonKnowledgeProfile:
        """Return a person's full knowledge profile.

        Raises:
            PersonNotFoundInGraphError: If no person with this ID exists in the graph.
        """

    @abstractmethod
    async def get_topics(self, page: int = 1, size: int = 50) -> tuple[list[TopicNode], int]:
        """Return a page of topics known to the graph plus the total count."""

    @abstractmethod
    async def get_persons(self, page: int = 1, size: int = 50) -> tuple[list[PersonNode], int]:
        """Return a page of persons known to the graph plus the total count."""

    @abstractmethod
    async def get_related_topics(self, topic: str, limit: int = 10) -> list[TopicNode]:
        """Return topics related to the given topic."""

    @abstractmethod
    async def get_documents_by_topic(
        self, topic: str, limit: int = 20
    ) -> list[DocumentNode]:
        """Return documents that reference the given topic."""

    # --- Write use cases (driven by inbound Kafka events) ---

    @abstractmethod
    async def register_interaction(
        self,
        person_id: str,
        person_name: str,
        topic_name: str,
        interaction_type: str,
        department: str | None = None,
        topic_description: str | None = None,
    ) -> None:
        """Record that a person interacted with a topic (knows about it or answered about it).

        Args:
            person_id: External Slack user ID of the person.
            person_name: Display name of the person.
            topic_name: Name of the topic.
            interaction_type: Either "knows" (KNOWS_ABOUT) or "answered" (ANSWERED_ABOUT).
            department: Optional department of the person.
            topic_description: Optional description of the topic.
        """

    @abstractmethod
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

    @abstractmethod
    async def register_channel_activity(
        self,
        person_id: str,
        person_name: str,
        channel_id: str,
        channel_name: str,
    ) -> None:
        """Record that a person is active in a channel."""
