"""Relationship type constants used when writing to the Neo4j knowledge graph.

Plain string constants (not an Enum) since they are used directly as Cypher
relationship type tokens by the adapter layer.
"""

KNOWS_ABOUT = "KNOWS_ABOUT"
"""Person -> Topic, weighted by how strongly the person is associated with it."""

WROTE = "WROTE"
"""Person -> Document, the person authored the document."""

ANSWERED_ABOUT = "ANSWERED_ABOUT"
"""Person -> Topic, the person answered an interview question about this topic."""

MENTIONED_IN = "MENTIONED_IN"
"""Topic -> Channel, the topic was mentioned or discussed in this channel."""

ACTIVE_IN = "ACTIVE_IN"
"""Person -> Channel, the person is active/participates in this channel."""

REFERENCES = "REFERENCES"
"""Document -> Topic, the document covers or references this topic."""
