"""Parses the LLM's final JSON answer into typed dossier domain objects.

The LLM is instructed (see ``llm_dossier_generator.SYSTEM_PROMPT``) to end the
conversation with a single JSON object of the shape::

    {
      "summary": "...",
      "sections": [
        {"section_type": "responsibilities", "title": "...", "responsibilities": ["..."]},
        {"section_type": "contacts", "title": "...", "contacts": [{"name": ..., "role": ...,
            "email": ..., "relationship": ...}]},
        {"section_type": "pending_tasks", "title": "...", "tasks": [{"description": ...,
            "priority": ..., "deadline": ...}]},
        {"section_type": "knowledge_areas", "title": "...", "areas": [{"topic": ...,
            "description": ..., "expertise_level": ...}]}
      ]
    }

This mirrors mcp-server's own ``DossierSection`` wire format (the
``generate_dossier`` tool's response), so both sides agree on one contract.

Every function here raises ``ValueError`` (or lets ``json.JSONDecodeError``,
a ``ValueError`` subclass, propagate) on any shape mismatch. The caller
treats that as an LLM failure and falls back to the deterministic generator.
"""

from __future__ import annotations

import json
import re

from app.domain.dossier.section import (
    Contact,
    ContactsSection,
    DossierSection,
    KnowledgeArea,
    KnowledgeAreasSection,
    PendingTask,
    PendingTasksSection,
    ResponsibilitiesSection,
)

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_llm_response(text: str) -> tuple[str | None, list[DossierSection]]:
    """Parse the model's final answer into a (summary, sections) tuple.

    Args:
        text: The raw text of the model's last message.

    Returns:
        A tuple of (summary, sections) ready to persist on the dossier.

    Raises:
        ValueError: If the text isn't a JSON object matching the expected shape.
    """
    payload = json.loads(_strip_fence(text))
    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object")

    summary = payload.get("summary")
    if summary is not None and not isinstance(summary, str):
        raise ValueError("'summary' must be a string or null")

    raw_sections = payload.get("sections", [])
    if not isinstance(raw_sections, list):
        raise ValueError("'sections' must be a list")

    return summary, [_section_from_dict(item) for item in raw_sections]


def _strip_fence(text: str) -> str:
    match = _JSON_FENCE.search(text)
    return match.group(1) if match else text.strip()


def _section_from_dict(item: object) -> DossierSection:
    if not isinstance(item, dict):
        raise ValueError(f"section entry must be an object, got {type(item).__name__}")

    title = item.get("title")
    if not isinstance(title, str) or not title:
        raise ValueError("section 'title' must be a non-empty string")

    section_type = item.get("section_type")
    if section_type == "responsibilities":
        responsibilities = item.get("responsibilities")
        if not isinstance(responsibilities, list) or not all(
            isinstance(r, str) for r in responsibilities
        ):
            raise ValueError("'responsibilities' must be a list of strings")
        return ResponsibilitiesSection(title=title, responsibilities=responsibilities)

    if section_type == "contacts":
        contacts = [_contact_from_dict(c) for c in _require_list(item, "contacts")]
        return ContactsSection(title=title, contacts=contacts)

    if section_type == "pending_tasks":
        tasks = [_pending_task_from_dict(t) for t in _require_list(item, "tasks")]
        return PendingTasksSection(title=title, tasks=tasks)

    if section_type == "knowledge_areas":
        areas = [_knowledge_area_from_dict(a) for a in _require_list(item, "areas")]
        return KnowledgeAreasSection(title=title, areas=areas)

    raise ValueError(f"unknown section type: {section_type!r}")


def _require_list(item: dict, key: str) -> list:
    value = item.get(key)
    if not isinstance(value, list):
        raise ValueError(f"'{key}' must be a list")
    return value


def _contact_from_dict(raw: object) -> Contact:
    if not isinstance(raw, dict):
        raise ValueError("contact entry must be an object")
    try:
        return Contact(
            name=raw["name"],
            role=raw["role"],
            email=raw["email"],
            relationship=raw["relationship"],
        )
    except KeyError as exc:
        raise ValueError(f"contact missing required field: {exc}") from exc


def _pending_task_from_dict(raw: object) -> PendingTask:
    if not isinstance(raw, dict):
        raise ValueError("pending task entry must be an object")
    try:
        return PendingTask(
            description=raw["description"],
            priority=raw["priority"],
            deadline=raw.get("deadline"),
        )
    except KeyError as exc:
        raise ValueError(f"pending task missing required field: {exc}") from exc


def _knowledge_area_from_dict(raw: object) -> KnowledgeArea:
    if not isinstance(raw, dict):
        raise ValueError("knowledge area entry must be an object")
    try:
        return KnowledgeArea(
            topic=raw["topic"],
            description=raw["description"],
            expertise_level=raw["expertise_level"],
        )
    except KeyError as exc:
        raise ValueError(f"knowledge area missing required field: {exc}") from exc
