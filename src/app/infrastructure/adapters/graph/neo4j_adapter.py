"""Neo4j adapter — concrete implementation of IGraphDatabasePort."""

from __future__ import annotations

import logging

from neo4j import AsyncDriver

from app.application.ports.graph_database import IGraphDatabasePort

logger = logging.getLogger(__name__)

# Default server-side timeout (seconds) for Cypher queries executed through
# this adapter. Guards against pathological/runaway queries (e.g. a topic
# connected to many experts each connected to many topics) hanging the
# request indefinitely. Not currently exposed via Settings — bump here if a
# legitimate query needs more headroom.
_QUERY_TIMEOUT_SECONDS = 10.0


class Neo4jAdapter(IGraphDatabasePort):
    """Concrete adapter that wraps a Neo4j AsyncDriver.

    Receives an already-initialised driver from the composition root (main.py
    lifespan) so the adapter itself stays free of configuration concerns.
    """

    def __init__(self, driver: AsyncDriver) -> None:
        """Initialise the adapter with a Neo4j async driver.

        Args:
            driver: An active ``neo4j.AsyncDriver`` instance.
        """
        self._driver = driver

    async def verify_connectivity(self) -> bool:
        """Verify that Neo4j is reachable.

        Returns:
            bool: True if the driver could connect successfully, False otherwise.
        """
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            logger.warning("Neo4j connectivity check failed", exc_info=True)
            return False

    async def execute_query(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> list[dict]:
        """Execute a Cypher query and return the results as plain dictionaries.

        Args:
            query: A Cypher query string.
            parameters: Optional mapping of query parameters.

        Returns:
            list[dict]: Each element is a record returned by the query.
        """
        result = await self._driver.execute_query(
            query, parameters or {}, timeout=_QUERY_TIMEOUT_SECONDS
        )
        return [record.data() for record in result.records]
