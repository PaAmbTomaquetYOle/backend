"""Knowledge graph bounded context — read-model value objects over Neo4j.

Unlike the offboarding/interview/dossier aggregates, these entities have no
lifecycle state machine: they mirror nodes and relationships living in Neo4j,
whose business value comes from the relationships between them rather than
from state transitions on a single entity.
"""

from .entities import ChannelNode, DocumentNode, PersonNode, TopicNode
from .query_results import ExpertResult, PersonKnowledgeProfile
from .relationships import (
    ACTIVE_IN,
    ANSWERED_ABOUT,
    KNOWS_ABOUT,
    MENTIONED_IN,
    REFERENCES,
    WROTE,
)

__all__ = [
    "ChannelNode",
    "DocumentNode",
    "PersonNode",
    "TopicNode",
    "ExpertResult",
    "PersonKnowledgeProfile",
    "ACTIVE_IN",
    "ANSWERED_ABOUT",
    "KNOWS_ABOUT",
    "MENTIONED_IN",
    "REFERENCES",
    "WROTE",
]
