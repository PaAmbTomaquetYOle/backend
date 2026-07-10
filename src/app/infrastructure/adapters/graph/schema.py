"""One-time Neo4j schema setup (uniqueness constraints) for the knowledge graph."""

from __future__ import annotations

from app.application.ports.graph_database import IGraphDatabasePort

_CONSTRAINTS = (
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS "
    "FOR (p:Person) REQUIRE p.person_id IS UNIQUE",
    "CREATE CONSTRAINT topic_name_unique IF NOT EXISTS "
    "FOR (t:Topic) REQUIRE t.name IS UNIQUE",
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS "
    "FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
    "CREATE CONSTRAINT channel_id_unique IF NOT EXISTS "
    "FOR (c:Channel) REQUIRE c.channel_id IS UNIQUE",
)


async def initialize_knowledge_graph_schema(graph_db: IGraphDatabasePort) -> None:
    """Create the uniqueness constraints backing the knowledge graph node types.

    Idempotent (``IF NOT EXISTS``) — safe to call on every application startup.

    Args:
        graph_db: The graph database port to run the constraint statements on.
    """
    for constraint in _CONSTRAINTS:
        await graph_db.execute_query(constraint)
