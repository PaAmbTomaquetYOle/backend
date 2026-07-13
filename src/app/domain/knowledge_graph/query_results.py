"""Typed results for knowledge graph queries — compositions of graph entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.knowledge_graph.entities import DocumentNode, PersonNode, TopicNode


@dataclass(frozen=True)
class ExpertResult:
    """A person recommended as an expert on a given topic, with a relevance score.

    ``first_seen``/``last_seen`` are the earliest/most recent time the
    underlying relationship(s) were recorded (SA-19 temporal groundwork).
    Both are ``None`` for relationships written before that change shipped —
    there is no retroactive history for pre-existing edges.
    """

    person: PersonNode
    topic: str
    score: float
    first_seen: datetime | None = None
    last_seen: datetime | None = None


@dataclass(frozen=True)
class PersonKnowledgeProfile:
    """A person's full knowledge footprint: topics they know and documents they wrote."""

    person: PersonNode
    topics: list[TopicNode] = field(default_factory=list)
    documents: list[DocumentNode] = field(default_factory=list)


@dataclass(frozen=True)
class PersonAnalytics:
    """Graph-analytics profile for a person, from a single GDS run (SA-19).

    Computed over a person-to-person projection (two persons linked when they
    share a topic) so the metrics describe how people relate to each other,
    not a mix of persons and topics:

    - ``community_id``: Louvain community — which knowledge cluster this
      person belongs to.
    - ``influence``: weighted PageRank — how relied-upon/authoritative this
      person is in the collaboration network.
    - ``broker_score``: betweenness centrality — how much this person bridges
      otherwise-disconnected communities. High broker_score + that person
      leaving means the connective tissue between communities disappears —
      the headline "who is riskiest to lose" signal for offboarding.
    """

    person_id: str
    community_id: int
    influence: float
    broker_score: float


@dataclass(frozen=True)
class SuccessorCandidate:
    """A person who could plausibly cover for another, ranked by topic overlap.

    ``similarity`` is a GDS Node Similarity (Jaccard-over-shared-topics) score
    in [0, 1] — answers "who else already knows what this person knows",
    the direct offboarding "who can cover for X" use case.
    """

    person: PersonNode
    similarity: float
