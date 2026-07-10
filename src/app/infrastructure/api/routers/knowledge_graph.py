"""HTTP endpoints for querying the knowledge graph.

Read-only, matching the offboarding write-convergence policy: all writes to
the graph (registering interactions, documents, channel activity) go through
Kafka — see ``domain/events/inbound_events.py``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.application.service_interfaces.knowledge_graph_service_interface import (
    IKnowledgeGraphService,
)
from app.infrastructure.adapters.auth.jwt_bearer import get_current_service
from app.infrastructure.api.dependencies import knowledge_graph_service_dependency
from app.infrastructure.api.schemas.knowledge_graph import (
    DocumentResponse,
    ExpertResponse,
    PersonKnowledgeProfileResponse,
    PersonPageResponse,
    TopicPageResponse,
    TopicResponse,
    document_to_response,
    expert_to_response,
    person_page_response,
    profile_to_response,
    topic_page_response,
    topic_to_response,
)

router = APIRouter(
    prefix="/knowledge-graph",
    tags=["knowledge-graph"],
    dependencies=[Depends(get_current_service)],
)

Service = Annotated[IKnowledgeGraphService, Depends(knowledge_graph_service_dependency)]


@router.get(
    "/experts",
    response_model=list[ExpertResponse],
    summary="Find experts for a topic",
)
async def get_experts(
        service: Service,
        topic: Annotated[str, Query(description="Topic name to find experts for")],
        limit: Annotated[int, Query(ge=1, le=100, description="Maximum experts to return")] = 10,
) -> list[ExpertResponse]:
    """Find the persons most associated with a topic, ranked by score."""
    experts = await service.get_experts_by_topic(topic, limit=limit)
    return [expert_to_response(e) for e in experts]


@router.get(
    "/persons",
    response_model=PersonPageResponse,
    summary="List persons known to the graph, paginated",
)
async def list_persons(
        service: Service,
        page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
        size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> PersonPageResponse:
    """List all persons known to the graph."""
    persons, total = await service.get_persons(page=page, size=size)
    return person_page_response(persons, page=page, size=size, total=total)


@router.get(
    "/persons/{person_id}",
    response_model=PersonKnowledgeProfileResponse,
    summary="Get a person's knowledge profile",
)
async def get_person_profile(
        person_id: str,
        service: Service,
) -> PersonKnowledgeProfileResponse:
    """Retrieve a person's full knowledge profile (topics and authored documents)."""
    profile = await service.get_person_profile(person_id)
    return profile_to_response(profile)


@router.get(
    "/topics",
    response_model=TopicPageResponse,
    summary="List topics known to the graph, paginated",
)
async def list_topics(
        service: Service,
        page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
        size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> TopicPageResponse:
    """List all topics known to the graph."""
    topics, total = await service.get_topics(page=page, size=size)
    return topic_page_response(topics, page=page, size=size, total=total)


@router.get(
    "/topics/{topic_name}/experts",
    response_model=list[ExpertResponse],
    summary="Find experts for a specific topic",
)
async def get_topic_experts(
        topic_name: str,
        service: Service,
        limit: Annotated[int, Query(ge=1, le=100, description="Maximum experts to return")] = 10,
) -> list[ExpertResponse]:
    """Find the persons most associated with the given topic, ranked by score."""
    experts = await service.get_experts_by_topic(topic_name, limit=limit)
    return [expert_to_response(e) for e in experts]


@router.get(
    "/topics/{topic_name}/related",
    response_model=list[TopicResponse],
    summary="Find topics related to a given topic",
)
async def get_related_topics(
        topic_name: str,
        service: Service,
        limit: Annotated[int, Query(ge=1, le=100, description="Maximum topics to return")] = 10,
) -> list[TopicResponse]:
    """Find topics related to the given topic (via shared experts)."""
    topics = await service.get_related_topics(topic_name, limit=limit)
    return [topic_to_response(t) for t in topics]


@router.get(
    "/topics/{topic_name}/documents",
    response_model=list[DocumentResponse],
    summary="Find documents that reference a given topic",
)
async def get_topic_documents(
        topic_name: str,
        service: Service,
        limit: Annotated[int, Query(ge=1, le=100, description="Maximum documents to return")] = 20,
) -> list[DocumentResponse]:
    """Find documents that reference the given topic."""
    documents = await service.get_documents_by_topic(topic_name, limit=limit)
    return [document_to_response(d) for d in documents]
