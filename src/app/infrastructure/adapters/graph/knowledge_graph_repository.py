"""Neo4j-backed implementation of IKnowledgeGraphRepository.

Composes IGraphDatabasePort (rather than talking to the Neo4j driver
directly) so it reuses the existing driver lifecycle and automatically
degrades to no-op behavior when Neo4j is unavailable (NoOpGraphAdapter).
"""

from __future__ import annotations

from app.application.ports.graph_database import IGraphDatabasePort
from app.application.ports.knowledge_graph import IKnowledgeGraphRepository
from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonKnowledgeProfile,
    PersonNode,
    TopicNode,
)
from app.domain.knowledge_graph.relationships import (
    ACTIVE_IN,
    ANSWERED_ABOUT,
    KNOWS_ABOUT,
    MENTIONED_IN,
    REFERENCES,
    WROTE,
)


class Neo4jKnowledgeGraphRepository(IKnowledgeGraphRepository):
    """Translates knowledge graph operations into parameterized Cypher queries."""

    def __init__(self, graph_db: IGraphDatabasePort) -> None:
        """Initialise the repository with the underlying graph database port.

        Args:
            graph_db: The low-level graph database port used to run Cypher.
        """
        self._graph_db = graph_db

    # --- Node operations (write) ---

    async def upsert_person(
        self, person_id: str, name: str, department: str | None = None
    ) -> None:
        """Create or update a Person node."""
        await self._graph_db.execute_query(
            """
            MERGE (p:Person {person_id: $person_id})
            SET p.name = $name, p.department = $department
            """,
            {"person_id": person_id, "name": name, "department": department},
        )

    async def upsert_topic(self, name: str, description: str | None = None) -> None:
        """Create or update a Topic node."""
        await self._graph_db.execute_query(
            """
            MERGE (t:Topic {name: $name})
            SET t.description = coalesce($description, t.description)
            """,
            {"name": name, "description": description},
        )

    async def upsert_document(
        self,
        document_id: str,
        title: str,
        url: str | None = None,
        source: str | None = None,
    ) -> None:
        """Create or update a Document node."""
        await self._graph_db.execute_query(
            """
            MERGE (d:Document {document_id: $document_id})
            SET d.title = $title, d.url = $url, d.source = $source
            """,
            {"document_id": document_id, "title": title, "url": url, "source": source},
        )

    async def upsert_channel(self, channel_id: str, name: str) -> None:
        """Create or update a Channel node."""
        await self._graph_db.execute_query(
            """
            MERGE (c:Channel {channel_id: $channel_id})
            SET c.name = $name
            """,
            {"channel_id": channel_id, "name": name},
        )

    # --- Relationship operations (write) ---

    async def register_expertise(
        self, person_id: str, topic_name: str, weight: float = 1.0
    ) -> None:
        """Create or strengthen a KNOWS_ABOUT relationship from a person to a topic."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (t:Topic {{name: $topic_name}})
            MERGE (p)-[r:{KNOWS_ABOUT}]->(t)
            ON CREATE SET r.weight = $weight
            ON MATCH SET r.weight = coalesce(r.weight, 0) + $weight
            """,
            {"person_id": person_id, "topic_name": topic_name, "weight": weight},
        )

    async def register_authorship(self, person_id: str, document_id: str) -> None:
        """Create a WROTE relationship from a person to a document."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (d:Document {{document_id: $document_id}})
            MERGE (p)-[:{WROTE}]->(d)
            """,
            {"person_id": person_id, "document_id": document_id},
        )

    async def register_answer(self, person_id: str, topic_name: str) -> None:
        """Create an ANSWERED_ABOUT relationship from a person to a topic."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (t:Topic {{name: $topic_name}})
            MERGE (p)-[:{ANSWERED_ABOUT}]->(t)
            """,
            {"person_id": person_id, "topic_name": topic_name},
        )

    async def register_topic_mention(self, topic_name: str, channel_id: str) -> None:
        """Create a MENTIONED_IN relationship from a topic to a channel."""
        await self._graph_db.execute_query(
            f"""
            MATCH (t:Topic {{name: $topic_name}}), (c:Channel {{channel_id: $channel_id}})
            MERGE (t)-[:{MENTIONED_IN}]->(c)
            """,
            {"topic_name": topic_name, "channel_id": channel_id},
        )

    async def register_activity(self, person_id: str, channel_id: str) -> None:
        """Create an ACTIVE_IN relationship from a person to a channel."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (c:Channel {{channel_id: $channel_id}})
            MERGE (p)-[:{ACTIVE_IN}]->(c)
            """,
            {"person_id": person_id, "channel_id": channel_id},
        )

    async def register_document_reference(self, document_id: str, topic_name: str) -> None:
        """Create a REFERENCES relationship from a document to a topic."""
        await self._graph_db.execute_query(
            f"""
            MATCH (d:Document {{document_id: $document_id}}), (t:Topic {{name: $topic_name}})
            MERGE (d)-[:{REFERENCES}]->(t)
            """,
            {"document_id": document_id, "topic_name": topic_name},
        )

    # --- Query operations (read) ---

    async def find_experts_by_topic(self, topic_name: str, limit: int = 10) -> list[ExpertResult]:
        """Find the persons most associated with a topic, ranked by score."""
        records = await self._graph_db.execute_query(
            f"""
            MATCH (p:Person)-[r:{KNOWS_ABOUT}|{ANSWERED_ABOUT}]->(t:Topic {{name: $topic_name}})
            RETURN p.person_id AS person_id, p.name AS name, p.department AS department,
                   sum(CASE WHEN type(r) = '{KNOWS_ABOUT}' THEN coalesce(r.weight, 1.0)
                            ELSE 1.0 END) AS score
            ORDER BY score DESC
            LIMIT $limit
            """,
            {"topic_name": topic_name, "limit": limit},
        )
        return [
            ExpertResult(
                person=PersonNode(
                    person_id=record["person_id"],
                    name=record["name"],
                    department=record.get("department"),
                ),
                topic=topic_name,
                score=record["score"],
            )
            for record in records
        ]

    async def find_topics_by_person(self, person_id: str) -> list[TopicNode]:
        """Find the topics a person is known to be associated with."""
        records = await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}})-[:{KNOWS_ABOUT}|{ANSWERED_ABOUT}]->(t:Topic)
            RETURN DISTINCT t.name AS name, t.description AS description
            """,
            {"person_id": person_id},
        )
        return [
            TopicNode(name=record["name"], description=record.get("description"))
            for record in records
        ]

    async def find_person_knowledge_profile(
        self, person_id: str
    ) -> PersonKnowledgeProfile | None:
        """Find a person's full knowledge profile (topics and authored documents)."""
        records = await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}})
            RETURN p.person_id AS person_id, p.name AS name, p.department AS department,
                   [(p)-[:{KNOWS_ABOUT}|{ANSWERED_ABOUT}]->(t:Topic) |
                       {{name: t.name, description: t.description}}] AS topics,
                   [(p)-[:{WROTE}]->(d:Document) |
                       {{document_id: d.document_id, title: d.title,
                         url: d.url, source: d.source}}] AS documents
            """,
            {"person_id": person_id},
        )
        if not records:
            return None
        record = records[0]
        return PersonKnowledgeProfile(
            person=PersonNode(
                person_id=record["person_id"],
                name=record["name"],
                department=record.get("department"),
            ),
            topics=[
                TopicNode(name=topic["name"], description=topic.get("description"))
                for topic in record["topics"]
            ],
            documents=[
                DocumentNode(
                    document_id=document["document_id"],
                    title=document["title"],
                    url=document.get("url"),
                    source=document.get("source"),
                )
                for document in record["documents"]
            ],
        )

    async def find_related_topics(self, topic_name: str, limit: int = 10) -> list[TopicNode]:
        """Find topics related to the given topic (via shared experts)."""
        records = await self._graph_db.execute_query(
            f"""
            MATCH (t:Topic {{name: $topic_name}})<-[:{KNOWS_ABOUT}|{ANSWERED_ABOUT}]-(:Person)
                  -[:{KNOWS_ABOUT}|{ANSWERED_ABOUT}]->(other:Topic)
            WHERE other.name <> $topic_name
            RETURN DISTINCT other.name AS name, other.description AS description
            LIMIT $limit
            """,
            {"topic_name": topic_name, "limit": limit},
        )
        return [
            TopicNode(name=record["name"], description=record.get("description"))
            for record in records
        ]

    async def find_documents_by_topic(
        self, topic_name: str, limit: int = 20
    ) -> list[DocumentNode]:
        """Find documents that reference the given topic."""
        records = await self._graph_db.execute_query(
            f"""
            MATCH (d:Document)-[:{REFERENCES}]->(t:Topic {{name: $topic_name}})
            RETURN DISTINCT d.document_id AS document_id, d.title AS title,
                   d.url AS url, d.source AS source
            LIMIT $limit
            """,
            {"topic_name": topic_name, "limit": limit},
        )
        return [
            DocumentNode(
                document_id=record["document_id"],
                title=record["title"],
                url=record.get("url"),
                source=record.get("source"),
            )
            for record in records
        ]

    async def find_all_topics(self, page: int = 1, size: int = 50) -> tuple[list[TopicNode], int]:
        """List all topics in the graph, paginated."""
        skip = (page - 1) * size
        count_records = await self._graph_db.execute_query(
            "MATCH (t:Topic) RETURN count(t) AS total"
        )
        total = count_records[0]["total"] if count_records else 0
        records = await self._graph_db.execute_query(
            """
            MATCH (t:Topic)
            RETURN t.name AS name, t.description AS description
            ORDER BY t.name
            SKIP $skip LIMIT $size
            """,
            {"skip": skip, "size": size},
        )
        topics = [
            TopicNode(name=record["name"], description=record.get("description"))
            for record in records
        ]
        return topics, total

    async def find_all_persons(
        self, page: int = 1, size: int = 50
    ) -> tuple[list[PersonNode], int]:
        """List all persons in the graph, paginated."""
        skip = (page - 1) * size
        count_records = await self._graph_db.execute_query(
            "MATCH (p:Person) RETURN count(p) AS total"
        )
        total = count_records[0]["total"] if count_records else 0
        records = await self._graph_db.execute_query(
            """
            MATCH (p:Person)
            RETURN p.person_id AS person_id, p.name AS name, p.department AS department
            ORDER BY p.name
            SKIP $skip LIMIT $size
            """,
            {"skip": skip, "size": size},
        )
        persons = [
            PersonNode(
                person_id=record["person_id"],
                name=record["name"],
                department=record.get("department"),
            )
            for record in records
        ]
        return persons, total
