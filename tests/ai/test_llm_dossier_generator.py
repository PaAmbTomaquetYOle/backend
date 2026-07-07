"""Tests for LLMDossierGenerator: the agentic, mcp-server-backed adapter."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.domain import (
    CompletedInterviewState,
    Interview,
    InterviewId,
    InterviewQuestion,
    OffboardingProcessId,
    ResponsibilitiesSection,
    SpeakerRoleEnum,
)
from app.infrastructure.adapters.ai import llm_dossier_generator as module
from app.infrastructure.adapters.ai.fake_dossier_generator import FakeDossierGenerator
from app.infrastructure.adapters.ai.llm_dossier_generator import LLMDossierGenerator


def _interview() -> Interview:
    return Interview(
        interview_id=InterviewId(),
        process_id=OffboardingProcessId(),
        state=CompletedInterviewState(),
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        turns=[
            InterviewQuestion(
                speaker_role=SpeakerRoleEnum.INTERVIEWER,
                timestamp=datetime.now(UTC),
                content="What are your main responsibilities?",
                order=0,
                answer_text="Lead the backend team",
            ),
        ],
    )


class _TextBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text

    def model_dump(self) -> dict:
        return {"type": "text", "text": self.text}


class _ToolUseBlock:
    type = "tool_use"

    def __init__(self, block_id: str, name: str, tool_input: dict) -> None:
        self.id = block_id
        self.name = name
        self.input = tool_input

    def model_dump(self) -> dict:
        return {"type": "tool_use", "id": self.id, "name": self.name, "input": self.input}


class _FakeMessage:
    def __init__(self, content: list, stop_reason: str) -> None:
        self.content = content
        self.stop_reason = stop_reason


class _FakeTool:
    def __init__(
        self, name: str, description: str = "desc", input_schema: dict | None = None
    ) -> None:
        self.name = name
        self.description = description
        self.inputSchema = input_schema or {"type": "object", "properties": {}}


class _FakeListToolsResult:
    def __init__(self, tools: list) -> None:
        self.tools = tools


class _FakeTextContent:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeCallToolResult:
    def __init__(self, text: str, is_error: bool = False) -> None:
        self.content = [_FakeTextContent(text)]
        self.isError = is_error


class _FakeClientSession:
    def __init__(self, tools: list, call_tool_results: dict | None = None) -> None:
        self._tools = tools
        self._call_tool_results = call_tool_results or {}
        self.calls: list[tuple[str, dict]] = []

    async def __aenter__(self) -> "_FakeClientSession":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    async def initialize(self) -> None:
        pass

    async def list_tools(self) -> _FakeListToolsResult:
        return _FakeListToolsResult(self._tools)

    async def call_tool(self, name: str, arguments: dict) -> _FakeCallToolResult:
        self.calls.append((name, arguments))
        return self._call_tool_results[name]


class _FakeStreamContext:
    async def __aenter__(self) -> tuple[None, None, None]:
        return (None, None, None)

    async def __aexit__(self, *exc_info) -> bool:
        return False


class _FakeAnthropicMessages:
    def __init__(self, responses: list[_FakeMessage]) -> None:
        self.create = AsyncMock(side_effect=responses)


class _FakeAnthropicClient:
    def __init__(self, responses: list[_FakeMessage]) -> None:
        self.messages = _FakeAnthropicMessages(responses)


def _patch_mcp(monkeypatch: pytest.MonkeyPatch, session: _FakeClientSession) -> None:
    monkeypatch.setattr(module, "streamablehttp_client", lambda url: _FakeStreamContext())
    monkeypatch.setattr(module, "ClientSession", lambda read, write: session)


def _generator(
    monkeypatch: pytest.MonkeyPatch, responses: list[_FakeMessage]
) -> LLMDossierGenerator:
    generator = LLMDossierGenerator(
        anthropic_api_key="test-key",
        model="test-model",
        mcp_server_url="http://localhost:8000/mcp",
        fallback=FakeDossierGenerator(),
    )
    monkeypatch.setattr(generator, "_client", _FakeAnthropicClient(responses))
    return generator


class TestLLMDossierGenerator:
    @pytest.mark.anyio
    async def test_final_answer_without_tool_use(self, monkeypatch: pytest.MonkeyPatch) -> None:
        final_json = json.dumps(
            {
                "summary": "Handover summary.",
                "sections": [
                    {
                        "type": "responsibilities",
                        "title": "Responsibilities",
                        "responsibilities": ["Lead the backend team"],
                    }
                ],
            }
        )
        session = _FakeClientSession(
            tools=[_FakeTool("get_dossier"), _FakeTool("test_search_query")]
        )
        _patch_mcp(monkeypatch, session)
        generator = _generator(monkeypatch, [_FakeMessage([_TextBlock(final_json)], "end_turn")])

        summary, sections = await generator.generate(_interview())

        assert summary == "Handover summary."
        assert len(sections) == 1
        assert isinstance(sections[0], ResponsibilitiesSection)

    @pytest.mark.anyio
    async def test_only_allow_listed_tools_are_exposed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeClientSession(
            tools=[_FakeTool("get_dossier"), _FakeTool("jira_auth"), _FakeTool("test_search_query")]
        )
        _patch_mcp(monkeypatch, session)
        captured = {}

        async def fake_create(**kwargs):
            captured["tools"] = kwargs["tools"]
            return _FakeMessage(
                [_TextBlock(json.dumps({"summary": None, "sections": []}))], "end_turn"
            )

        generator = _generator(monkeypatch, [])
        generator._client.messages.create = AsyncMock(side_effect=fake_create)

        await generator.generate(_interview())

        tool_names = {tool["name"] for tool in captured["tools"]}
        assert tool_names == {"get_dossier", "test_search_query"}

    @pytest.mark.anyio
    async def test_executes_tool_call_then_returns_final_answer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeClientSession(
            tools=[_FakeTool("get_dossier")],
            call_tool_results={"get_dossier": _FakeCallToolResult('{"results": []}')},
        )
        _patch_mcp(monkeypatch, session)
        final_json = json.dumps({"summary": "Enriched summary.", "sections": []})
        responses = [
            _FakeMessage(
                [_ToolUseBlock("tool-1", "get_dossier", {"employee_name": "Jane"})], "tool_use"
            ),
            _FakeMessage([_TextBlock(final_json)], "end_turn"),
        ]
        generator = _generator(monkeypatch, responses)

        summary, sections = await generator.generate(_interview())

        assert summary == "Enriched summary."
        assert sections == []
        assert session.calls == [("get_dossier", {"employee_name": "Jane"})]

    @pytest.mark.anyio
    async def test_falls_back_on_malformed_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        session = _FakeClientSession(tools=[])
        _patch_mcp(monkeypatch, session)
        generator = _generator(monkeypatch, [_FakeMessage([_TextBlock("not json")], "end_turn")])

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1
        assert isinstance(sections[0], ResponsibilitiesSection)

    @pytest.mark.anyio
    async def test_falls_back_when_tool_iterations_exhausted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeClientSession(
            tools=[_FakeTool("get_dossier")],
            call_tool_results={"get_dossier": _FakeCallToolResult("{}")},
        )
        _patch_mcp(monkeypatch, session)
        always_tool_use = _FakeMessage([_ToolUseBlock("tool-1", "get_dossier", {})], "tool_use")
        generator = LLMDossierGenerator(
            anthropic_api_key="test-key",
            model="test-model",
            mcp_server_url="http://localhost:8000/mcp",
            fallback=FakeDossierGenerator(),
            max_tool_iterations=2,
        )
        monkeypatch.setattr(
            generator,
            "_client",
            _FakeAnthropicClient([always_tool_use, always_tool_use, always_tool_use]),
        )

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1

    @pytest.mark.anyio
    async def test_falls_back_on_mcp_connection_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(url: str):
            raise ConnectionError("mcp-server unreachable")

        monkeypatch.setattr(module, "streamablehttp_client", _raise)
        generator = _generator(monkeypatch, [])

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1

    @pytest.mark.anyio
    async def test_falls_back_on_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import asyncio

        session = _FakeClientSession(tools=[])
        _patch_mcp(monkeypatch, session)

        async def _slow_create(**kwargs):
            await asyncio.sleep(1)
            return _FakeMessage([_TextBlock("{}")], "end_turn")

        generator = LLMDossierGenerator(
            anthropic_api_key="test-key",
            model="test-model",
            mcp_server_url="http://localhost:8000/mcp",
            fallback=FakeDossierGenerator(),
            timeout_seconds=0.01,
        )
        generator._client.messages.create = AsyncMock(side_effect=_slow_create)

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1
