"""Unit tests for knowledge graph API endpoints — mock service, test HTTP layer only.

All writes to the knowledge graph are Kafka-only — see
``tests/events/handlers/test_knowledge_*_handler.py``. This module only
covers the REST (read-only) endpoints.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.domain.exceptions.knowledge_graph import PersonNotFoundInGraphError
from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonKnowledgeProfile,
    PersonNode,
    TopicNode,
)
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import knowledge_graph_service_dependency
from app.main import create_app


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=IKnowledgeGraphService)


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[knowledge_graph_service_dependency] = lambda: mock_service
    app.dependency_overrides[get_current_service] = lambda: {
        "iss": "test-service", "aud": "offboardme-backend"
    }
    return TestClient(app)


class TestGetExperts:
    def test_200_returns_experts(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_experts_by_topic.return_value = [
            ExpertResult(person=PersonNode(person_id="U1", name="Alice"), topic="k8s", score=2.0)
        ]

        r = client.get("/api/v1/knowledge-graph/experts?topic=k8s")

        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["person"]["person_id"] == "U1"
        assert body[0]["score"] == 2.0

    def test_forwards_topic_and_limit(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_experts_by_topic.return_value = []

        r = client.get("/api/v1/knowledge-graph/experts?topic=k8s&limit=5")

        assert r.status_code == 200
        mock_service.get_experts_by_topic.assert_awaited_once_with("k8s", limit=5)

    def test_422_missing_topic(self, client: TestClient) -> None:
        r = client.get("/api/v1/knowledge-graph/experts")
        assert r.status_code == 422


class TestListPersons:
    def test_200_returns_page(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_persons.return_value = (
            [PersonNode(person_id="U1", name="Alice")],
            1,
        )

        r = client.get("/api/v1/knowledge-graph/persons")

        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["person_id"] == "U1"


class TestGetPersonProfile:
    def test_200_returns_profile(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_person_profile.return_value = PersonKnowledgeProfile(
            person=PersonNode(person_id="U1", name="Alice"),
            topics=[TopicNode(name="k8s")],
            documents=[DocumentNode(document_id="D1", title="Runbook")],
        )

        r = client.get("/api/v1/knowledge-graph/persons/U1")

        assert r.status_code == 200
        body = r.json()
        assert body["person"]["person_id"] == "U1"
        assert body["topics"][0]["name"] == "k8s"
        assert body["documents"][0]["document_id"] == "D1"

    def test_404_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_person_profile.side_effect = PersonNotFoundInGraphError("U404")

        r = client.get("/api/v1/knowledge-graph/persons/U404")

        assert r.status_code == 404


class TestListTopics:
    def test_200_returns_page(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_topics.return_value = ([TopicNode(name="k8s")], 1)

        r = client.get("/api/v1/knowledge-graph/topics")

        assert r.status_code == 200
        assert r.json()["total"] == 1


class TestTopicExperts:
    def test_200_returns_experts(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_experts_by_topic.return_value = []

        r = client.get("/api/v1/knowledge-graph/topics/k8s/experts")

        assert r.status_code == 200
        assert r.json() == []


class TestRelatedTopics:
    def test_200_returns_related_topics(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_related_topics.return_value = [TopicNode(name="terraform")]

        r = client.get("/api/v1/knowledge-graph/topics/k8s/related")

        assert r.status_code == 200
        assert r.json()[0]["name"] == "terraform"


class TestTopicDocuments:
    def test_200_returns_documents(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_documents_by_topic.return_value = [
            DocumentNode(document_id="D1", title="Runbook")
        ]

        r = client.get("/api/v1/knowledge-graph/topics/k8s/documents")

        assert r.status_code == 200
        assert r.json()[0]["document_id"] == "D1"
