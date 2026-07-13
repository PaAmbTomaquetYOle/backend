"""Request/response schemas for knowledge graph endpoints."""

import math
from datetime import datetime

from pydantic import BaseModel

from app.domain.knowledge_graph import (
    DocumentNode,
    ExpertResult,
    PersonAnalytics,
    PersonKnowledgeProfile,
    PersonNode,
    SuccessorCandidate,
    TopicNode,
)


class PersonResponse(BaseModel):
    """Response body representing a person node."""

    person_id: str
    name: str
    department: str | None = None


class TopicResponse(BaseModel):
    """Response body representing a topic node."""

    name: str
    description: str | None = None


class DocumentResponse(BaseModel):
    """Response body representing a document node."""

    document_id: str
    title: str
    url: str | None = None
    source: str | None = None


class ExpertResponse(BaseModel):
    """Response body representing a person recommended as an expert on a topic."""

    person: PersonResponse
    topic: str
    score: float
    first_seen: datetime | None = None
    last_seen: datetime | None = None


class PersonAnalyticsResponse(BaseModel):
    """Response body representing a person's graph-analytics profile (SA-19)."""

    person_id: str
    community_id: int
    influence: float
    broker_score: float


class SuccessorCandidateResponse(BaseModel):
    """Response body representing a candidate to cover for another person."""

    person: PersonResponse
    similarity: float


class PersonKnowledgeProfileResponse(BaseModel):
    """Response body representing a person's full knowledge profile."""

    person: PersonResponse
    topics: list[TopicResponse]
    documents: list[DocumentResponse]


class TopicPageResponse(BaseModel):
    """Paginated list response for topics."""

    items: list[TopicResponse]
    page: int
    size: int
    total: int
    total_pages: int


class PersonPageResponse(BaseModel):
    """Paginated list response for persons."""

    items: list[PersonResponse]
    page: int
    size: int
    total: int
    total_pages: int


def person_to_response(person: PersonNode) -> PersonResponse:
    """Convert a domain PersonNode to its API response schema."""
    return PersonResponse(
        person_id=person.person_id, name=person.name, department=person.department
    )


def topic_to_response(topic: TopicNode) -> TopicResponse:
    """Convert a domain TopicNode to its API response schema."""
    return TopicResponse(name=topic.name, description=topic.description)


def document_to_response(document: DocumentNode) -> DocumentResponse:
    """Convert a domain DocumentNode to its API response schema."""
    return DocumentResponse(
        document_id=document.document_id,
        title=document.title,
        url=document.url,
        source=document.source,
    )


def expert_to_response(expert: ExpertResult) -> ExpertResponse:
    """Convert a domain ExpertResult to its API response schema."""
    return ExpertResponse(
        person=person_to_response(expert.person),
        topic=expert.topic,
        score=expert.score,
        first_seen=expert.first_seen,
        last_seen=expert.last_seen,
    )


def person_analytics_to_response(analytics: PersonAnalytics) -> PersonAnalyticsResponse:
    """Convert a domain PersonAnalytics to its API response schema."""
    return PersonAnalyticsResponse(
        person_id=analytics.person_id,
        community_id=analytics.community_id,
        influence=analytics.influence,
        broker_score=analytics.broker_score,
    )


def successor_candidate_to_response(
    candidate: SuccessorCandidate,
) -> SuccessorCandidateResponse:
    """Convert a domain SuccessorCandidate to its API response schema."""
    return SuccessorCandidateResponse(
        person=person_to_response(candidate.person), similarity=candidate.similarity
    )


def profile_to_response(profile: PersonKnowledgeProfile) -> PersonKnowledgeProfileResponse:
    """Convert a domain PersonKnowledgeProfile to its API response schema."""
    return PersonKnowledgeProfileResponse(
        person=person_to_response(profile.person),
        topics=[topic_to_response(t) for t in profile.topics],
        documents=[document_to_response(d) for d in profile.documents],
    )


def topic_page_response(
    topics: list[TopicNode], page: int, size: int, total: int
) -> TopicPageResponse:
    """Build a paginated topic list response."""
    total_pages = math.ceil(total / size) if size else 0
    return TopicPageResponse(
        items=[topic_to_response(t) for t in topics],
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
    )


def person_page_response(
    persons: list[PersonNode], page: int, size: int, total: int
) -> PersonPageResponse:
    """Build a paginated person list response."""
    total_pages = math.ceil(total / size) if size else 0
    return PersonPageResponse(
        items=[person_to_response(p) for p in persons],
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
    )
