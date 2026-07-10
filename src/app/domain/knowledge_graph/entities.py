"""Frozen value objects mirroring node types in the Neo4j knowledge graph."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonNode:
    """A Person node — an employee identified by their external Slack user ID."""

    person_id: str
    name: str
    department: str | None = None


@dataclass(frozen=True)
class TopicNode:
    """A Topic node — a skill or knowledge area, identified by its name."""

    name: str
    description: str | None = None


@dataclass(frozen=True)
class DocumentNode:
    """A Document node — a piece of written knowledge (dossier, SOP, article, ...)."""

    document_id: str
    title: str
    url: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class ChannelNode:
    """A Channel node — a Slack channel identified by its external Slack channel ID."""

    channel_id: str
    name: str
