"""Graph database port — abstract interface for graph database operations."""

from abc import ABC, abstractmethod


class IGraphDatabasePort(ABC):
    """Abstract interface for graph database operations.

    Provides a minimal surface to verify connectivity and execute arbitrary
    Cypher queries. Domain-specific graph repositories should program against
    this port and be wired to a concrete adapter at the composition root.
    """

    @abstractmethod
    async def verify_connectivity(self) -> bool:
        """Check whether the graph database is reachable.

        Returns:
            bool: True if the database accepted the connection, False otherwise.
        """

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> list[dict]:
        """Execute a Cypher query and return the results as a list of records.

        Args:
            query: A Cypher query string.
            parameters: Optional mapping of query parameters.

        Returns:
            list[dict]: Each element is a record returned by the query,
                represented as a plain Python dictionary.
        """
