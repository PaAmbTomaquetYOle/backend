"""Tests for knowledge graph domain value objects."""

from app.domain.knowledge_graph import (
    ChannelNode,
    DocumentNode,
    ExpertResult,
    PersonKnowledgeProfile,
    PersonNode,
    TopicNode,
)


def test_person_node_defaults() -> None:
    person = PersonNode(person_id="U1", name="Alice")
    assert person.department is None


def test_topic_node_defaults() -> None:
    topic = TopicNode(name="kubernetes")
    assert topic.description is None


def test_document_node_defaults() -> None:
    document = DocumentNode(document_id="D1", title="Runbook")
    assert document.url is None
    assert document.source is None


def test_channel_node() -> None:
    channel = ChannelNode(channel_id="C1", name="#infra")
    assert channel.channel_id == "C1"
    assert channel.name == "#infra"


def test_expert_result() -> None:
    person = PersonNode(person_id="U1", name="Alice")
    result = ExpertResult(person=person, topic="kubernetes", score=2.5)
    assert result.person is person
    assert result.score == 2.5


def test_person_knowledge_profile_defaults_to_empty_lists() -> None:
    person = PersonNode(person_id="U1", name="Alice")
    profile = PersonKnowledgeProfile(person=person)
    assert profile.topics == []
    assert profile.documents == []


def test_value_objects_are_frozen() -> None:
    person = PersonNode(person_id="U1", name="Alice")
    other = PersonNode(person_id="U1", name="Alice")
    assert person == other
