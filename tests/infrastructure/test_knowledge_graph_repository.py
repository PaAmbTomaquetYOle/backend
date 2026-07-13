"""Tests for Neo4jKnowledgeGraphRepository and NoOpKnowledgeGraphRepository."""

from unittest.mock import AsyncMock

import pytest
from neo4j.exceptions import Neo4jError

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
async def test_register_expertise_stamps_created_and_last_seen(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = []

    await repo.register_expertise("U1", "kubernetes")

    query, _ = graph_db.execute_query.call_args[0]
    assert "r.created_at = datetime()" in query
    assert "r.last_seen_at = datetime()" in query


@pytest.mark.anyio
async def test_register_authorship_stamps_created_and_last_seen(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = []

    await repo.register_authorship("U1", "D1")

    query, _ = graph_db.execute_query.call_args[0]
    assert "r.created_at = datetime()" in query
    assert "r.last_seen_at = datetime()" in query


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
async def test_find_experts_by_topic_maps_first_and_last_seen(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = [
        {
            "person_id": "U1",
            "name": "Alice",
            "department": "SRE",
            "score": 3.0,
            "first_seen": "2024-01-01T00:00:00",
            "last_seen": "2024-06-01T00:00:00",
        },
        {"person_id": "U2", "name": "Bob", "department": None, "score": 1.0},
    ]

    results = await repo.find_experts_by_topic("kubernetes", limit=5)

    assert results[0].first_seen == "2024-01-01T00:00:00"
    assert results[0].last_seen == "2024-06-01T00:00:00"
    # Edges predating the timestamp change have neither field recorded.
    assert results[1].first_seen is None
    assert results[1].last_seen is None

    query, _ = graph_db.execute_query.call_args[0]
    assert "min(r.created_at) AS first_seen" in query
    assert "max(r.last_seen_at) AS last_seen" in query


@pytest.mark.anyio
async def test_find_experts_by_topic_converts_neo4j_temporal_values() -> None:
    class _FakeNeo4jDateTime:
        def __init__(self, native):
            self._native = native

        def to_native(self):
            return self._native

    graph_db = AsyncMock(spec=IGraphDatabasePort)
    native_dt = object()
    graph_db.execute_query.return_value = [
        {
            "person_id": "U1",
            "name": "Alice",
            "department": None,
            "score": 1.0,
            "first_seen": _FakeNeo4jDateTime(native_dt),
            "last_seen": None,
        }
    ]
    repo = Neo4jKnowledgeGraphRepository(graph_db)

    results = await repo.find_experts_by_topic("kubernetes")

    assert results[0].first_seen is native_dt


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
    graph_db.execute_query.return_value = [
        {
            "total": 2,
            "rows": [
                {"name": "kubernetes", "description": None},
                {"name": "terraform", "description": None},
            ],
        }
    ]

    topics, total = await repo.find_all_topics(page=1, size=50)

    assert total == 2
    assert [t.name for t in topics] == ["kubernetes", "terraform"]
    assert graph_db.execute_query.call_count == 1


@pytest.mark.anyio
async def test_find_all_topics_preserves_total_on_out_of_range_page(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = [{"total": 2, "rows": []}]

    topics, total = await repo.find_all_topics(page=99, size=50)

    assert (topics, total) == ([], 2)


@pytest.mark.anyio
async def test_find_all_persons_returns_page_and_total(
    repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
) -> None:
    graph_db.execute_query.return_value = [
        {
            "total": 2,
            "rows": [
                {"person_id": "U1", "name": "Alice", "department": "SRE"},
                {"person_id": "U2", "name": "Bob", "department": None},
            ],
        }
    ]

    persons, total = await repo.find_all_persons(page=1, size=50)

    assert total == 2
    assert [(p.person_id, p.name, p.department) for p in persons] == [
        ("U1", "Alice", "SRE"),
        ("U2", "Bob", None),
    ]
    assert graph_db.execute_query.call_count == 1


class TestComputePersonAnalytics:
    @pytest.mark.anyio
    async def test_merges_louvain_pagerank_and_betweenness_by_person_id(
        self, repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
    ) -> None:
        async def side_effect(query: str, params: dict | None = None) -> list[dict]:
            if "gds.louvain.stream" in query:
                return [
                    {"person_id": "U1", "community_id": 0},
                    {"person_id": "U2", "community_id": 1},
                ]
            if "gds.pageRank.stream" in query:
                return [{"person_id": "U1", "influence": 1.5}]
            if "gds.betweenness.stream" in query:
                return [{"person_id": "U1", "broker_score": 2.0}]
            return []  # exists/drop, project, final drop

        graph_db.execute_query.side_effect = side_effect

        results = await repo.compute_person_analytics()
        by_id = {r.person_id: r for r in results}

        assert by_id["U1"].community_id == 0
        assert by_id["U1"].influence == 1.5
        assert by_id["U1"].broker_score == 2.0
        # U2 has no PageRank/betweenness row (e.g. isolated in that computation) — defaults apply.
        assert by_id["U2"].community_id == 1
        assert by_id["U2"].influence == 0.0
        assert by_id["U2"].broker_score == 0.0

    @pytest.mark.anyio
    async def test_degrades_to_empty_list_when_gds_procedure_missing(
        self, repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
    ) -> None:
        async def side_effect(query: str, params: dict | None = None) -> list[dict]:
            if "gds.louvain.stream" in query:
                raise Neo4jError("Neo.ClientError.Procedure.ProcedureNotFound")
            return []

        graph_db.execute_query.side_effect = side_effect

        assert await repo.compute_person_analytics() == []

    @pytest.mark.anyio
    async def test_drops_projection_even_when_gds_fails(
        self, repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
    ) -> None:
        calls: list[str] = []

        async def side_effect(query: str, params: dict | None = None) -> list[dict]:
            calls.append(query)
            if "gds.louvain.stream" in query:
                raise Neo4jError("boom")
            return []

        graph_db.execute_query.side_effect = side_effect

        await repo.compute_person_analytics()

        assert any("gds.graph.drop" in q for q in calls)


class TestFindSuccessorCandidates:
    @pytest.mark.anyio
    async def test_maps_similarity_results_for_the_given_person(
        self, repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
    ) -> None:
        async def side_effect(query: str, params: dict | None = None) -> list[dict]:
            if "gds.nodeSimilarity.stream" in query:
                return [
                    {"person_id": "U2", "name": "Bob", "department": "SRE", "similarity": 0.8},
                ]
            return []

        graph_db.execute_query.side_effect = side_effect

        results = await repo.find_successor_candidates("U1", limit=5)

        assert len(results) == 1
        assert results[0].person.person_id == "U2"
        assert results[0].similarity == 0.8

    @pytest.mark.anyio
    async def test_degrades_to_empty_list_when_gds_procedure_missing(
        self, repo: Neo4jKnowledgeGraphRepository, graph_db: AsyncMock
    ) -> None:
        async def side_effect(query: str, params: dict | None = None) -> list[dict]:
            if "gds.nodeSimilarity.stream" in query:
                raise Neo4jError("Neo.ClientError.Procedure.ProcedureNotFound")
            return []

        graph_db.execute_query.side_effect = side_effect

        assert await repo.find_successor_candidates("U1") == []


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
    assert await repo.compute_person_analytics() == []
    assert await repo.find_successor_candidates("U1") == []
