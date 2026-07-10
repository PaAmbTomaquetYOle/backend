"""Tests for the DB health endpoint."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.application.ports.graph_database import IGraphDatabasePort
from app.infrastructure.adapters.events.kafka_event_publisher import KafkaEventPublisher
from app.infrastructure.api.dependencies import get_session, graph_database_dependency


@pytest.fixture
def mock_session() -> Mock:
    return Mock()


@pytest.fixture
def mock_graph_db() -> AsyncMock:
    port = AsyncMock(spec=IGraphDatabasePort)
    port.verify_connectivity.return_value = True
    return port


@pytest.fixture
def client_with_mocks(
    client: TestClient, mock_session: Mock, mock_graph_db: AsyncMock
) -> TestClient:
    client.app.dependency_overrides[get_session] = lambda: mock_session
    client.app.dependency_overrides[graph_database_dependency] = lambda: mock_graph_db
    
    original_publisher = getattr(client.app.state, "event_publisher", None)
    client.app.state.event_publisher = Mock(spec=KafkaEventPublisher)
    
    yield client
    
    client.app.dependency_overrides.clear()
    client.app.state.event_publisher = original_publisher


def test_health_db_returns_ok_when_both_dbs_are_up(
    client_with_mocks: TestClient,
    mock_session: Mock,
    mock_graph_db: AsyncMock,
) -> None:
    mock_session.execute.return_value = None

    response = client_with_mocks.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json() == {"postgres": "ok", "neo4j": "ok", "kafka": "ok"}
    mock_session.execute.assert_called_once()
    mock_graph_db.verify_connectivity.assert_awaited_once()


def test_health_db_returns_503_when_postgres_fails(
    client_with_mocks: TestClient,
    mock_session: Mock,
    mock_graph_db: AsyncMock,
) -> None:
    mock_session.execute.side_effect = Exception("DB Down")

    response = client_with_mocks.get("/api/v1/health/db")

    assert response.status_code == 503
    assert response.json() == {"postgres": "error", "neo4j": "ok", "kafka": "ok"}


def test_health_db_returns_503_when_neo4j_fails(
    client_with_mocks: TestClient,
    mock_session: Mock,
    mock_graph_db: AsyncMock,
) -> None:
    mock_graph_db.verify_connectivity.return_value = False

    response = client_with_mocks.get("/api/v1/health/db")

    assert response.status_code == 503
    assert response.json() == {"postgres": "ok", "neo4j": "error", "kafka": "ok"}

def test_health_db_returns_503_when_kafka_fails(
    client_with_mocks: TestClient,
    mock_session: Mock,
    mock_graph_db: AsyncMock,
) -> None:
    client_with_mocks.app.state.event_publisher = Mock()  # Not a KafkaEventPublisher

    response = client_with_mocks.get("/api/v1/health/db")

    assert response.status_code == 503
    assert response.json() == {"postgres": "ok", "neo4j": "ok", "kafka": "error"}
