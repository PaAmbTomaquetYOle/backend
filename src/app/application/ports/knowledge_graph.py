"""Knowledge graph repository port — business-level graph read/write operations.

Distinct from ``IGraphDatabasePort`` (application/ports/graph_database.py),
which is the low-level infrastructure seam for raw Cypher execution. This port
speaks the knowledge graph's own vocabulary (persons, topics, documents,
channels) so application services never construct Cypher themselves.
"""

from abc import ABC, abstractmethod

from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonAnalytics,
    PersonKnowledgeProfile,
    PersonNode,
    SuccessorCandidate,
    TopicNode,
)


class IKnowledgeGraphRepository(ABC):
    """Abstract interface for reading and writing the knowledge graph.

    All write (upsert/register) operations must be idempotent, since inbound
    Kafka events are delivered at-least-once.
    """

    # --- Node operations (write) ---

    @abstractmethod
    async def upsert_person(
        self, person_id: str, name: str, department: str | None = None
    ) -> None:
        """Create or update a Person node."""

    @abstractmethod
    async def upsert_topic(self, name: str, description: str | None = None) -> None:
        """Create or update a Topic node."""

    @abstractmethod
    async def upsert_document(
        self,
        document_id: str,
        title: str,
        url: str | None = None,
        source: str | None = None,
    ) -> None:
        """Create or update a Document node."""

    @abstractmethod
    async def upsert_channel(self, channel_id: str, name: str) -> None:
        """Create or update a Channel node."""

    # --- Relationship operations (write) ---

    @abstractmethod
    async def register_expertise(
        self, person_id: str, topic_name: str, weight: float = 1.0
    ) -> None:
        """Create or strengthen a KNOWS_ABOUT relationship from a person to a topic."""

    @abstractmethod
    async def register_authorship(self, person_id: str, document_id: str) -> None:
        """Create a WROTE relationship from a person to a document."""

    @abstractmethod
    async def register_answer(self, person_id: str, topic_name: str) -> None:
        """Create an ANSWERED_ABOUT relationship from a person to a topic."""

    @abstractmethod
    async def register_topic_mention(self, topic_name: str, channel_id: str) -> None:
        """Create a MENTIONED_IN relationship from a topic to a channel."""

    @abstractmethod
    async def register_activity(self, person_id: str, channel_id: str) -> None:
        """Create an ACTIVE_IN relationship from a person to a channel."""

    @abstractmethod
    async def register_document_reference(self, document_id: str, topic_name: str) -> None:
        """Create a REFERENCES relationship from a document to a topic."""

    # --- Query operations (read) ---

    @abstractmethod
    async def find_experts_by_topic(self, topic_name: str, limit: int = 10) -> list[ExpertResult]:
        """Find the persons most associated with a topic, ranked by score."""

    @abstractmethod
    async def find_topics_by_person(self, person_id: str) -> list[TopicNode]:
        """Find the topics a person is known to be associated with."""

    @abstractmethod
    async def find_person_knowledge_profile(
        self, person_id: str
    ) -> PersonKnowledgeProfile | None:
        """Find a person's full knowledge profile (topics and authored documents)."""

    @abstractmethod
    async def find_related_topics(self, topic_name: str, limit: int = 10) -> list[TopicNode]:
        """Find topics related to the given topic (e.g. via shared experts or documents)."""

    @abstractmethod
    async def find_documents_by_topic(
        self, topic_name: str, limit: int = 20
    ) -> list[DocumentNode]:
        """Find documents that reference the given topic."""

    @abstractmethod
    async def find_all_topics(self, page: int = 1, size: int = 50) -> tuple[list[TopicNode], int]:
        """List all topics in the graph, paginated.

        Returns:
            tuple[list[TopicNode], int]: The page of topics and the total count.
        """

    @abstractmethod
    async def find_all_persons(
        self, page: int = 1, size: int = 50
    ) -> tuple[list[PersonNode], int]:
        """List all persons in the graph, paginated.

        Returns:
            tuple[list[PersonNode], int]: The page of persons and the total count.
        """

    # --- Graph analytics (read, GDS-backed, SA-19) ---

    @abstractmethod
    async def compute_person_analytics(self) -> list[PersonAnalytics]:
        """Run community detection and centrality over the person network.

        Projects a person-to-person graph (two persons linked when they share
        a topic) and runs Louvain (community), weighted PageRank (influence),
        and betweenness centrality (broker_score) over it in a single pass.

        Returns:
            list[PersonAnalytics]: One entry per person with graph data.
                Empty if the GDS plugin is unavailable — callers must treat
                that as "analytics not available", not an error.
        """

    @abstractmethod
    async def find_successor_candidates(
        self, person_id: str, limit: int = 5
    ) -> list[SuccessorCandidate]:
        """Find persons whose topic footprint most overlaps with the given person.

        Uses GDS Node Similarity (Jaccard over shared topics) to answer "who
        else already knows what this person knows" — candidates to cover for
        them during an offboarding.

        Args:
            person_id: External Slack user ID of the person leaving/being covered.
            limit: Maximum number of candidates to return.

        Returns:
            list[SuccessorCandidate]: Ranked by similarity, descending. Empty
                if the GDS plugin is unavailable or the person has no overlap
                with anyone else.
        """
