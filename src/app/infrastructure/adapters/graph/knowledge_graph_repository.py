"""Neo4j-backed implementation of IKnowledgeGraphRepository.

Composes IGraphDatabasePort (rather than talking to the Neo4j driver
directly) so it reuses the existing driver lifecycle and automatically
degrades to no-op behavior when Neo4j is unavailable (NoOpGraphAdapter).
"""

from __future__ import annotations

import logging
import uuid

from neo4j.exceptions import Neo4jError

from app.application.ports.graph_database import IGraphDatabasePort
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
from app.domain.knowledge_graph.relationships import (
    ACTIVE_IN,
    ANSWERED_ABOUT,
    KNOWS_ABOUT,
    MENTIONED_IN,
    REFERENCES,
    WROTE,
)

logger = logging.getLogger(__name__)

# Name prefix for the ephemeral person-to-person GDS projections used by the
# analytics/successor queries below. Suffixed with a random token per call so
# concurrent requests never collide on the same named graph.
_PERSON_PROJECTION_PREFIX = "sa19-person-network"

# Cypher fragment projecting a person-to-person graph: two persons are linked
# (undirected, once) when they both know about or answered about the same
# topic, weighted by how many topics they share. Running Louvain/PageRank/
# betweenness over this monopartite view (instead of the raw bipartite
# Person-Topic graph) is what makes "community"/"influence"/"broker" mean
# "how this person relates to other people" rather than mixing in topics.
_PERSON_NETWORK_NODE_QUERY = "MATCH (p:Person) RETURN id(p) AS id"
_KNOWS_OR_ANSWERED = f"{KNOWS_ABOUT}|{ANSWERED_ABOUT}"
_PERSON_NETWORK_REL_QUERY = f"""
MATCH (p1:Person)-[:{_KNOWS_OR_ANSWERED}]->(t:Topic)<-[:{_KNOWS_OR_ANSWERED}]-(p2:Person)
WHERE id(p1) < id(p2)
RETURN id(p1) AS source, id(p2) AS target, count(DISTINCT t) AS weight
"""


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
            ON CREATE SET r.weight = $weight, r.created_at = datetime(), r.last_seen_at = datetime()
            ON MATCH SET r.weight = coalesce(r.weight, 0) + $weight, r.last_seen_at = datetime()
            """,
            {"person_id": person_id, "topic_name": topic_name, "weight": weight},
        )

    async def register_authorship(self, person_id: str, document_id: str) -> None:
        """Create a WROTE relationship from a person to a document."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (d:Document {{document_id: $document_id}})
            MERGE (p)-[r:{WROTE}]->(d)
            ON CREATE SET r.created_at = datetime(), r.last_seen_at = datetime()
            ON MATCH SET r.last_seen_at = datetime()
            """,
            {"person_id": person_id, "document_id": document_id},
        )

    async def register_answer(self, person_id: str, topic_name: str) -> None:
        """Create an ANSWERED_ABOUT relationship from a person to a topic."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (t:Topic {{name: $topic_name}})
            MERGE (p)-[r:{ANSWERED_ABOUT}]->(t)
            ON CREATE SET r.created_at = datetime(), r.last_seen_at = datetime()
            ON MATCH SET r.last_seen_at = datetime()
            """,
            {"person_id": person_id, "topic_name": topic_name},
        )

    async def register_topic_mention(self, topic_name: str, channel_id: str) -> None:
        """Create a MENTIONED_IN relationship from a topic to a channel."""
        await self._graph_db.execute_query(
            f"""
            MATCH (t:Topic {{name: $topic_name}}), (c:Channel {{channel_id: $channel_id}})
            MERGE (t)-[r:{MENTIONED_IN}]->(c)
            ON CREATE SET r.created_at = datetime(), r.last_seen_at = datetime()
            ON MATCH SET r.last_seen_at = datetime()
            """,
            {"topic_name": topic_name, "channel_id": channel_id},
        )

    async def register_activity(self, person_id: str, channel_id: str) -> None:
        """Create an ACTIVE_IN relationship from a person to a channel."""
        await self._graph_db.execute_query(
            f"""
            MATCH (p:Person {{person_id: $person_id}}), (c:Channel {{channel_id: $channel_id}})
            MERGE (p)-[r:{ACTIVE_IN}]->(c)
            ON CREATE SET r.created_at = datetime(), r.last_seen_at = datetime()
            ON MATCH SET r.last_seen_at = datetime()
            """,
            {"person_id": person_id, "channel_id": channel_id},
        )

    async def register_document_reference(self, document_id: str, topic_name: str) -> None:
        """Create a REFERENCES relationship from a document to a topic."""
        await self._graph_db.execute_query(
            f"""
            MATCH (d:Document {{document_id: $document_id}}), (t:Topic {{name: $topic_name}})
            MERGE (d)-[r:{REFERENCES}]->(t)
            ON CREATE SET r.created_at = datetime(), r.last_seen_at = datetime()
            ON MATCH SET r.last_seen_at = datetime()
            """,
            {"document_id": document_id, "topic_name": topic_name},
        )

    # --- Query operations (read) ---

    @staticmethod
    def _to_native_datetime(value: object) -> object:
        """Normalize a Neo4j temporal value to a stdlib ``datetime`` (or pass through).

        The driver returns ``neo4j.time.DateTime`` for Cypher ``datetime()``
        values, which exposes ``to_native()``. Plain ``None``/strings (e.g. in
        unit tests that mock the graph port directly) pass through unchanged.
        """
        to_native = getattr(value, "to_native", None)
        return to_native() if callable(to_native) else value

    async def find_experts_by_topic(self, topic_name: str, limit: int = 10) -> list[ExpertResult]:
        """Find the persons most associated with a topic, ranked by score."""
        records = await self._graph_db.execute_query(
            f"""
            MATCH (p:Person)-[r:{KNOWS_ABOUT}|{ANSWERED_ABOUT}]->(t:Topic {{name: $topic_name}})
            RETURN p.person_id AS person_id, p.name AS name, p.department AS department,
                   sum(CASE WHEN type(r) = '{KNOWS_ABOUT}' THEN coalesce(r.weight, 1.0)
                            ELSE 1.0 END) AS score,
                   min(r.created_at) AS first_seen, max(r.last_seen_at) AS last_seen
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
                first_seen=self._to_native_datetime(record.get("first_seen")),
                last_seen=self._to_native_datetime(record.get("last_seen")),
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
        """List all topics in the graph, paginated.

        Uses two uncorrelated ``CALL {}`` subqueries (count + collected data
        page) so a single round-trip yields exactly one row with both
        ``total`` and ``rows`` — unlike a single linear query, ``total``
        survives even when ``skip`` is past the end of the result set.
        """
        skip = (page - 1) * size
        records = await self._graph_db.execute_query(
            """
            CALL { MATCH (t:Topic) RETURN count(t) AS total }
            CALL {
                MATCH (t:Topic)
                WITH t ORDER BY t.name
                SKIP $skip LIMIT $size
                RETURN collect({name: t.name, description: t.description}) AS rows
            }
            RETURN total, rows
            """,
            {"skip": skip, "size": size},
        )
        if not records:
            return [], 0
        record = records[0]
        topics = [
            TopicNode(name=row["name"], description=row.get("description"))
            for row in record["rows"]
        ]
        return topics, record["total"]

    async def find_all_persons(
        self, page: int = 1, size: int = 50
    ) -> tuple[list[PersonNode], int]:
        """List all persons in the graph, paginated.

        See ``find_all_topics`` for why the count and data page are combined
        via two uncorrelated ``CALL {}`` subqueries in a single query.
        """
        skip = (page - 1) * size
        records = await self._graph_db.execute_query(
            """
            CALL { MATCH (p:Person) RETURN count(p) AS total }
            CALL {
                MATCH (p:Person)
                WITH p ORDER BY p.name
                SKIP $skip LIMIT $size
                RETURN collect({
                    person_id: p.person_id, name: p.name, department: p.department
                }) AS rows
            }
            RETURN total, rows
            """,
            {"skip": skip, "size": size},
        )
        if not records:
            return [], 0
        record = records[0]
        persons = [
            PersonNode(
                person_id=row["person_id"],
                name=row["name"],
                department=row.get("department"),
            )
            for row in record["rows"]
        ]
        return persons, record["total"]

    # --- Graph analytics (read, GDS-backed, SA-19) ---

    async def _project_person_network(self) -> str:
        """Project an ephemeral person-to-person graph and return its handle name.

        Drops any stale projection under the same name first (defensive —
        should not happen since names are per-call, but a prior crash could
        leave one behind) and lets the caller drop it in a ``finally``.
        """
        graph_name = f"{_PERSON_PROJECTION_PREFIX}-{uuid.uuid4().hex}"
        await self._graph_db.execute_query(
            """
            CALL gds.graph.exists($graph_name) YIELD exists
            WITH exists WHERE exists
            CALL gds.graph.drop($graph_name) YIELD graphName
            RETURN graphName
            """,
            {"graph_name": graph_name},
        )
        await self._graph_db.execute_query(
            "CALL gds.graph.project.cypher($graph_name, $node_query, $rel_query) "
            "YIELD graphName",
            {
                "graph_name": graph_name,
                "node_query": _PERSON_NETWORK_NODE_QUERY,
                "rel_query": _PERSON_NETWORK_REL_QUERY,
            },
        )
        return graph_name

    async def _drop_projection(self, graph_name: str) -> None:
        """Drop a named GDS graph projection, tolerating it already being gone."""
        try:
            await self._graph_db.execute_query(
                "CALL gds.graph.drop($graph_name, false) YIELD graphName",
                {"graph_name": graph_name},
            )
        except Neo4jError:
            logger.warning("Failed to drop GDS projection %s", graph_name, exc_info=True)

    async def compute_person_analytics(self) -> list[PersonAnalytics]:
        """Run Louvain + weighted PageRank + betweenness over the person network.

        Degrades to an empty list (rather than raising) when the GDS plugin
        is not installed or any other GDS-side error occurs — analytics are
        an enhancement, not a required capability (see IKnowledgeGraphRepository).
        """
        graph_name: str | None = None
        try:
            graph_name = await self._project_person_network()
            records = await self._graph_db.execute_query(
                """
                CALL gds.louvain.stream($graph_name, {relationshipWeightProperty: 'weight'})
                YIELD nodeId, communityId
                WITH gds.util.asNode(nodeId) AS person, communityId
                RETURN person.person_id AS person_id, communityId AS community_id
                """,
                {"graph_name": graph_name},
            )
            communities = {r["person_id"]: r["community_id"] for r in records}

            pagerank_records = await self._graph_db.execute_query(
                """
                CALL gds.pageRank.stream($graph_name, {relationshipWeightProperty: 'weight'})
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) AS person, score
                RETURN person.person_id AS person_id, score AS influence
                """,
                {"graph_name": graph_name},
            )
            influence = {r["person_id"]: r["influence"] for r in pagerank_records}

            betweenness_records = await self._graph_db.execute_query(
                """
                CALL gds.betweenness.stream($graph_name)
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) AS person, score
                RETURN person.person_id AS person_id, score AS broker_score
                """,
                {"graph_name": graph_name},
            )
            broker_scores = {r["person_id"]: r["broker_score"] for r in betweenness_records}

            person_ids = communities.keys() | influence.keys() | broker_scores.keys()
            return [
                PersonAnalytics(
                    person_id=person_id,
                    community_id=communities.get(person_id, -1),
                    influence=influence.get(person_id, 0.0),
                    broker_score=broker_scores.get(person_id, 0.0),
                )
                for person_id in person_ids
            ]
        except Neo4jError:
            logger.warning(
                "GDS person analytics unavailable (plugin missing or query failed) — "
                "degrading to an empty result",
                exc_info=True,
            )
            return []
        finally:
            if graph_name is not None:
                await self._drop_projection(graph_name)

    async def find_successor_candidates(
        self, person_id: str, limit: int = 5
    ) -> list[SuccessorCandidate]:
        """Find persons most similar to ``person_id`` via GDS Node Similarity.

        Degrades to an empty list when GDS is unavailable, mirroring
        ``compute_person_analytics``.
        """
        graph_name: str | None = None
        try:
            graph_name = await self._project_person_network()
            records = await self._graph_db.execute_query(
                """
                CALL gds.nodeSimilarity.stream($graph_name, {relationshipWeightProperty: 'weight'})
                YIELD node1, node2, similarity
                WITH gds.util.asNode(node1) AS source, gds.util.asNode(node2) AS target, similarity
                WHERE source.person_id = $person_id
                RETURN target.person_id AS person_id, target.name AS name,
                       target.department AS department, similarity
                ORDER BY similarity DESC
                LIMIT $limit
                """,
                {"graph_name": graph_name, "person_id": person_id, "limit": limit},
            )
            return [
                SuccessorCandidate(
                    person=PersonNode(
                        person_id=record["person_id"],
                        name=record["name"],
                        department=record.get("department"),
                    ),
                    similarity=record["similarity"],
                )
                for record in records
            ]
        except Neo4jError:
            logger.warning(
                "GDS successor candidates unavailable (plugin missing or query failed) — "
                "degrading to an empty result",
                exc_info=True,
            )
            return []
        finally:
            if graph_name is not None:
                await self._drop_projection(graph_name)
