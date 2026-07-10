"""Tests for Neo4j graph adapters."""

from unittest.mock import AsyncMock, Mock

import pytest
from neo4j import AsyncDriver, Record

from app.infrastructure.adapters.graph.neo4j_adapter import Neo4jAdapter
from app.infrastructure.adapters.graph.noop_graph_adapter import NoOpGraphAdapter


@pytest.fixture
def mock_driver() -> AsyncMock:
    return AsyncMock(spec=AsyncDriver)


@pytest.mark.anyio
async def test_neo4j_adapter_verify_connectivity_success(mock_driver: AsyncMock) -> None:
    adapter = Neo4jAdapter(mock_driver)
    mock_driver.verify_connectivity.return_value = None

    result = await adapter.verify_connectivity()

    assert result is True
    mock_driver.verify_connectivity.assert_awaited_once()


@pytest.mark.anyio
async def test_neo4j_adapter_verify_connectivity_failure(mock_driver: AsyncMock) -> None:
    adapter = Neo4jAdapter(mock_driver)
    mock_driver.verify_connectivity.side_effect = Exception("Connection refused")

    result = await adapter.verify_connectivity()

    assert result is False
    mock_driver.verify_connectivity.assert_awaited_once()


@pytest.mark.anyio
async def test_neo4j_adapter_execute_query(mock_driver: AsyncMock) -> None:
    adapter = Neo4jAdapter(mock_driver)

    mock_result = AsyncMock()
    mock_record = Mock(spec=Record)
    mock_record.data.return_value = {"id": 1, "name": "Test"}
    mock_result.records = [mock_record]
    mock_driver.execute_query.return_value = mock_result

    query = "MATCH (n) RETURN n"
    params = {"skip": 0}

    results = await adapter.execute_query(query, params)

    assert results == [{"id": 1, "name": "Test"}]
    mock_driver.execute_query.assert_awaited_once_with(query, params)


@pytest.mark.anyio
async def test_noop_graph_adapter_verify_connectivity() -> None:
    adapter = NoOpGraphAdapter()
    result = await adapter.verify_connectivity()
    assert result is False


@pytest.mark.anyio
async def test_noop_graph_adapter_execute_query() -> None:
    adapter = NoOpGraphAdapter()
    results = await adapter.execute_query("MATCH (n) RETURN n")
    assert results == []
