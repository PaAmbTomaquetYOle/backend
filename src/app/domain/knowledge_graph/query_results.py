"""Typed results for knowledge graph queries — compositions of graph entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.knowledge_graph.entities import DocumentNode, PersonNode, TopicNode


@dataclass(frozen=True)
class ExpertResult:
    """A person recommended as an expert on a given topic, with a relevance score."""

    person: PersonNode
    topic: str
    score: float


@dataclass(frozen=True)
class PersonKnowledgeProfile:
    """A person's full knowledge footprint: topics they know and documents they wrote."""

    person: PersonNode
    topics: list[TopicNode] = field(default_factory=list)
    documents: list[DocumentNode] = field(default_factory=list)
