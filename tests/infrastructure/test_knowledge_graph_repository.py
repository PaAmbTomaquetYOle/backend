"""Tests for Neo4jKnowledgeGraphRepository and NoOpKnowledgeGraphRepository."""

from unittest.mock import AsyncMock

import pytest

from app.application.ports.graph_database import IGraphDatabasePort
from app.domain.knowledge_graph import TopicNode
from app.infrastructure.adapters.graph.knowledge_graph_repository import (
    Neo4jKnowledgeGraphRepository,
)
from app.infrastructure.adapters.graph.noop_knowledge_graph_repository import (
    NoOpKnowledgeGraphRepository,
)


@pytest.fixture
def graph_db() -> AsyncMock:
    return AsyncMock(spec=IGraphDatabasePort)


@pytest.fixture
def repo(graph_db: AsyncMock) -> Neo4jKnowledgeGraphRepository:
    return Neo4jKnowledgeGraphRepository(graph_db)


@pytest.mark.anyio
async def test_upsert_person_passes_parameters(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = []

    await repo.upsert_person("U1", "Alice", department="SRE")

    query, params = graph_db.execute_query.call_args[0]
    assert "MERGE (p:Person" in query
    assert params == {"person_id": "U1", "name": "Alice", "department": "SRE"}


@pytest.mark.anyio
async def test_register_expertise_passes_default_weight(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = []

    await repo.register_expertise("U1", "kubernetes")

    query, params = graph_db.execute_query.call_args[0]
    assert "KNOWS_ABOUT" in query
    assert params == {"person_id": "U1", "topic_name": "kubernetes", "weight": 1.0}


@pytest.mark.anyio
async def test_find_experts_by_topic_maps_records_to_expert_results(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = [
        {"person_id": "U1", "name": "Alice", "department": "SRE", "score": 3.0},
        {"person_id": "U2", "name": "Bob", "department": None, "score": 1.0},
    ]

    results = await repo.find_experts_by_topic("kubernetes", limit=5)

    assert len(results) == 2
    assert results[0].person.person_id == "U1"
    assert results[0].topic == "kubernetes"
    assert results[0].score == 3.0
    assert results[1].person.department is None

    _, params = graph_db.execute_query.call_args[0]
    assert params == {"topic_name": "kubernetes", "limit": 5}


@pytest.mark.anyio
async def test_find_person_knowledge_profile_returns_none_when_not_found(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = []

    profile = await repo.find_person_knowledge_profile("U404")

    assert profile is None


@pytest.mark.anyio
async def test_find_person_knowledge_profile_maps_topics_and_documents(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = [
        {
            "person_id": "U1",
            "name": "Alice",
            "department": "SRE",
            "topics": [{"name": "kubernetes", "description": None}],
            "documents": [
                {"document_id": "D1", "title": "Runbook", "url": None, "source": "confluence"}
            ],
        }
    ]

    profile = await repo.find_person_knowledge_profile("U1")

    assert profile is not None
    assert profile.person.person_id == "U1"
    assert profile.topics == [TopicNode(name="kubernetes", description=None)]
    assert profile.documents[0].document_id == "D1"


@pytest.mark.anyio
async def test_find_all_topics_returns_page_and_total(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.side_effect = [
        [{"total": 2}],
        [
            {"name": "kubernetes", "description": None},
            {"name": "terraform", "description": None},
        ],
    ]

    topics, total = await repo.find_all_topics(page=1, size=50)

    assert total == 2
    assert [t.name for t in topics] == ["kubernetes", "terraform"]


@pytest.mark.anyio
async def test_noop_knowledge_graph_repository_writes_are_silent() -> None:
    repo = NoOpKnowledgeGraphRepository()

    await repo.upsert_person("U1", "Alice")
    await repo.register_expertise("U1", "kubernetes")


@pytest.mark.anyio
async def test_noop_knowledge_graph_repository_reads_return_empty() -> None:
    repo = NoOpKnowledgeGraphRepository()

    assert await repo.find_experts_by_topic("kubernetes") == []
    assert await repo.find_person_knowledge_profile("U1") is None
    assert await repo.find_all_topics() == ([], 0)
    assert await repo.find_all_persons() == ([], 0)
