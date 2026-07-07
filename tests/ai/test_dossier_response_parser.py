"""Tests for the LLM JSON response -> DossierSection parsing."""

import json

import pytest

from app.domain import (
    ContactsSection,
    KnowledgeAreasSection,
    PendingTasksSection,
    ResponsibilitiesSection,
)
from app.infrastructure.adapters.ai.dossier_response_parser import parse_llm_response


class TestParseLlmResponse:
    def test_parses_all_section_types(self) -> None:
        payload = {
            "summary": "Handover summary.",
            "sections": [
                {
                    "section_type": "responsibilities",
                    "title": "Responsibilities",
                    "responsibilities": ["Own the backend", "Run on-call"],
                },
                {
                    "section_type": "contacts",
                    "title": "Contacts",
                    "contacts": [
                        {
                            "name": "Jane Doe",
                            "role": "Manager",
                            "email": "jane@example.com",
                            "relationship": "Manager",
                        }
                    ],
                },
                {
                    "section_type": "pending_tasks",
                    "title": "Pending",
                    "tasks": [
                        {
                            "description": "Finish migration",
                            "priority": "high",
                            "deadline": "2026-08-01",
                        }
                    ],
                },
                {
                    "section_type": "knowledge_areas",
                    "title": "Knowledge",
                    "areas": [
                        {
                            "topic": "Kafka",
                            "description": "Event infra",
                            "expertise_level": "expert",
                        }
                    ],
                },
            ],
        }

        summary, sections = parse_llm_response(json.dumps(payload))

        assert summary == "Handover summary."
        assert len(sections) == 4
        assert isinstance(sections[0], ResponsibilitiesSection)
        assert sections[0].responsibilities == ["Own the backend", "Run on-call"]
        assert isinstance(sections[1], ContactsSection)
        assert sections[1].contacts[0].email == "jane@example.com"
        assert isinstance(sections[2], PendingTasksSection)
        assert sections[2].tasks[0].priority == "high"
        assert isinstance(sections[3], KnowledgeAreasSection)
        assert sections[3].areas[0].topic == "Kafka"

    def test_strips_markdown_json_fence(self) -> None:
        text = '```json\n{"summary": null, "sections": []}\n```'

        summary, sections = parse_llm_response(text)

        assert summary is None
        assert sections == []

    def test_missing_sections_key_defaults_to_empty_list(self) -> None:
        summary, sections = parse_llm_response(json.dumps({"summary": "ok"}))

        assert summary == "ok"
        assert sections == []

    def test_non_object_payload_raises(self) -> None:
        with pytest.raises(ValueError, match="JSON object"):
            parse_llm_response(json.dumps(["not", "an", "object"]))

    def test_unknown_section_type_raises(self) -> None:
        payload = {"summary": None, "sections": [{"section_type": "bogus", "title": "X"}]}

        with pytest.raises(ValueError, match="unknown section type"):
            parse_llm_response(json.dumps(payload))

    def test_section_missing_title_raises(self) -> None:
        payload = {
            "summary": None,
            "sections": [{"section_type": "responsibilities", "responsibilities": []}],
        }

        with pytest.raises(ValueError, match="title"):
            parse_llm_response(json.dumps(payload))

    def test_contact_missing_field_raises(self) -> None:
        payload = {
            "summary": None,
            "sections": [
                {
                    "section_type": "contacts",
                    "title": "Contacts",
                    "contacts": [{"name": "Jane", "role": "Manager"}],
                }
            ],
        }

        with pytest.raises(ValueError, match="missing required field"):
            parse_llm_response(json.dumps(payload))

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_llm_response("not json at all")
