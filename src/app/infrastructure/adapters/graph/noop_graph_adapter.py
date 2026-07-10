"""No-op graph adapter — fallback when Neo4j is unavailable."""

from __future__ import annotations

import logging

from app.application.ports.graph_database import IGraphDatabasePort

logger = logging.getLogger(__name__)


class NoOpGraphAdapter(IGraphDatabasePort):
    """Fallback adapter used when the Neo4j driver cannot be initialised.

    All operations are no-ops that return safe default values, following the
    same pattern as ``NoOpEventPublisher`` for Kafka. This allows the
    application to start and serve requests even when Neo4j is down.
    """

    async def verify_connectivity(self) -> bool:
        """Always returns False — no real connection is held.

        Returns:
            bool: Always False.
        """
        return False

    async def execute_query(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> list[dict]:
        """No-op query execution — returns an empty list.

        Args:
            query: Ignored Cypher query string.
            parameters: Ignored query parameters.

        Returns:
            list[dict]: Always an empty list.
        """
        logger.warning(
            "NoOpGraphAdapter.execute_query called — Neo4j is not available. "
            "Query was: %s",
            query,
        )
        return []
