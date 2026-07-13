"""Tests for LLMDossierGenerator: a thin MCP client of mcp-server's generate_dossier tool."""

import json
from datetime import UTC, datetime
from unittest.mock import Mock

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


class _FakeTextContent:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeCallToolResult:
    def __init__(self, text: str, is_error: bool = False) -> None:
        self.content = [_FakeTextContent(text)]
        self.isError = is_error


class _FakeClientSession:
    def __init__(self, result: _FakeCallToolResult) -> None:
        self._result = result
        self.calls: list[tuple[str, dict]] = []

    async def __aenter__(self) -> "_FakeClientSession":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    async def initialize(self) -> None:
        pass

    async def call_tool(self, name: str, arguments: dict) -> _FakeCallToolResult:
        self.calls.append((name, arguments))
        return self._result


class _FakeStreamContext:
    async def __aenter__(self) -> tuple[None, None, None]:
        return (None, None, None)

    async def __aexit__(self, *exc_info) -> bool:
        return False


def _patch_mcp(monkeypatch: pytest.MonkeyPatch, session: _FakeClientSession) -> None:
    monkeypatch.setattr(module, "streamablehttp_client", lambda url: _FakeStreamContext())
    monkeypatch.setattr(module, "ClientSession", lambda read, write: session)


class TestLLMDossierGenerator:
    @pytest.mark.anyio
    async def test_calls_generate_dossier_tool_and_parses_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        final_json = json.dumps(
            {
                "summary": "Handover summary.",
                "sections": [
                    {
                        "section_type": "responsibilities",
                        "title": "Responsibilities",
                        "responsibilities": ["Lead the backend team"],
                    }
                ],
            }
        )
        session = _FakeClientSession(_FakeCallToolResult(final_json))
        _patch_mcp(monkeypatch, session)
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp", fallback=FakeDossierGenerator()
        )

        summary, sections = await generator.generate(_interview())

        assert summary == "Handover summary."
        assert len(sections) == 1
        assert isinstance(sections[0], ResponsibilitiesSection)
        tool_name, arguments = session.calls[0]
        assert tool_name == "generate_dossier"
        assert "Lead the backend team" in arguments["interview_transcript"]
        assert arguments["review_scope"] == "offboarding"

    @pytest.mark.anyio
    async def test_forwards_review_scope_to_the_tool(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        empty_result = json.dumps({"summary": None, "sections": []})
        session = _FakeClientSession(_FakeCallToolResult(empty_result))
        _patch_mcp(monkeypatch, session)
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp", fallback=FakeDossierGenerator()
        )

        await generator.generate(_interview(), "annual")

        _, arguments = session.calls[0]
        assert arguments["review_scope"] == "annual"

    @pytest.mark.anyio
    async def test_falls_back_when_tool_call_reports_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeClientSession(_FakeCallToolResult("boom", is_error=True))
        _patch_mcp(monkeypatch, session)
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp", fallback=FakeDossierGenerator()
        )

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1
        assert isinstance(sections[0], ResponsibilitiesSection)

    @pytest.mark.anyio
    async def test_falls_back_on_malformed_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        session = _FakeClientSession(_FakeCallToolResult("not json"))
        _patch_mcp(monkeypatch, session)
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp", fallback=FakeDossierGenerator()
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
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp", fallback=FakeDossierGenerator()
        )

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1

    @pytest.mark.anyio
    async def test_falls_back_records_a_dossier_fallback_metric(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """BE-20: a fallback must be visible outside the logs via IMetricsPort."""
        from app.application.ports.metrics import FailureKind

        def _raise(url: str):
            raise ConnectionError("mcp-server unreachable")

        monkeypatch.setattr(module, "streamablehttp_client", _raise)
        metrics = Mock()
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp",
            fallback=FakeDossierGenerator(),
            metrics=metrics,
        )

        await generator.generate(_interview())

        metrics.increment_failure.assert_called_once()
        args, kwargs = metrics.increment_failure.call_args
        assert args[0] == FailureKind.DOSSIER_FALLBACK

    @pytest.mark.anyio
    async def test_falls_back_on_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import asyncio

        class _SlowClientSession(_FakeClientSession):
            async def call_tool(self, name: str, arguments: dict) -> _FakeCallToolResult:
                await asyncio.sleep(1)
                return await super().call_tool(name, arguments)

        session = _SlowClientSession(_FakeCallToolResult("{}"))
        _patch_mcp(monkeypatch, session)
        generator = LLMDossierGenerator(
            mcp_server_url="http://localhost:8000/mcp",
            fallback=FakeDossierGenerator(),
            timeout_seconds=0.01,
        )

        summary, sections = await generator.generate(_interview())

        assert "1" in summary
        assert len(sections) == 1
