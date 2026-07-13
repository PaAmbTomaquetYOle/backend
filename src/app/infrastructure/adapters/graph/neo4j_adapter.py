"""Neo4j adapter — concrete implementation of IGraphDatabasePort."""

from __future__ import annotations

import logging

from neo4j import AsyncDriver
from neo4j.exceptions import DriverError, Neo4jError

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.graph_database import IGraphDatabasePort
from app.application.ports.metrics import FailureKind, IMetricsPort

logger = logging.getLogger(__name__)

# Default server-side timeout (seconds) for Cypher queries executed through
# this adapter. Guards against pathological/runaway queries (e.g. a topic
# connected to many experts each connected to many topics) hanging the
# request indefinitely. Not currently exposed via Settings — bump here if a
# legitimate query needs more headroom.
_QUERY_TIMEOUT_SECONDS = 10.0


class _VerifyConnectivityOperation(ObservedOperation[bool]):
    """Checks Neo4j connectivity, recording a metric and returning False on failure."""

    def __init__(self, metrics: IMetricsPort | None, driver: AsyncDriver) -> None:
        super().__init__(metrics)
        self._driver = driver

    def _expected_exceptions(self) -> tuple[type[Exception], ...]:
        return (Neo4jError, DriverError)

    async def _execute(self) -> bool:
        await self._driver.verify_connectivity()
        return True

    def _failure_kind(self) -> FailureKind:
        return FailureKind.NEO4J_CONNECTIVITY

    def _log_failure(self, exc: Exception) -> None:
        logger.warning("Neo4j connectivity check failed", exc_info=True)

    async def _recover(self, exc: Exception) -> bool:
        return False


class Neo4jAdapter(IGraphDatabasePort):
    """Concrete adapter that wraps a Neo4j AsyncDriver.

    Receives an already-initialised driver from the composition root (main.py
    lifespan) so the adapter itself stays free of configuration concerns.
    """

    def __init__(self, driver: AsyncDriver, metrics: IMetricsPort | None = None) -> None:
        """Initialise the adapter with a Neo4j async driver.

        Args:
            driver: An active ``neo4j.AsyncDriver`` instance.
            metrics: Optional port for recording a failed connectivity check.
                If None, the failure is still logged but not counted (BE-20).
        """
        self._driver = driver
        self._metrics = metrics

    async def verify_connectivity(self) -> bool:
        """Verify that Neo4j is reachable.

        Returns:
            bool: True if the driver could connect successfully, False otherwise.
        """
        return await _VerifyConnectivityOperation(self._metrics, self._driver).run()

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
