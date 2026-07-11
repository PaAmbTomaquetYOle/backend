"""MCP-backed implementation of IDossierGenerator.

The model itself does not live in the backend. This adapter is a thin MCP
*client* of ``mcp-server``'s ``generate_dossier`` tool: the LLM, its system
prompt, and its own context-gathering tools (prior dossiers, SOP search) all
live in mcp-server (``DossierGenerationService``). The backend only formats
the interview transcript, calls the tool, and maps the JSON result to typed
DossierSection objects (see ``dossier_response_parser``).

Any failure (connection, timeout, tool error, malformed response) is caught
and delegated to the configured fallback generator, so a flaky mcp-server
never breaks the Kafka consumer's flow.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.application.observability.observed_operation import ObservedOperation
from app.application.ports.dossier_generator import DossierScope, IDossierGenerator
from app.application.ports.metrics import FailureKind, IMetricsPort
from app.domain.dossier.section import DossierSection
from app.domain.interview.interview import Interview
from app.domain.interview.turn import InterviewNote, InterviewQuestion
from app.infrastructure.adapters.ai.dossier_response_parser import parse_llm_response

logger = logging.getLogger(__name__)


class DossierGenerationOperation(ObservedOperation[tuple[str | None, list[DossierSection]]]):
    """Runs the mcp-server round trip, falling back to a default generator on any failure.

    Deliberately keeps the base class' broad `Exception` catch instead of
    narrowing it: the round trip can fail in ways that span multiple
    unrelated layers (TCP connection refused, MCP protocol/tool error,
    `asyncio.TimeoutError` from the wrapping `wait_for`, malformed JSON in
    `parse_llm_response`), and every one of them must degrade to the
    fallback generator rather than breaking the Kafka consumer's flow — see
    CLAUDE.md, "AI dossier generation is pluggable".
    """

    def __init__(
        self,
        metrics: IMetricsPort | None,
        mcp_call: Callable[[], Awaitable[tuple[str | None, list[DossierSection]]]],
        timeout_seconds: float,
        fallback: IDossierGenerator,
        interview: Interview,
        scope: DossierScope,
    ) -> None:
        super().__init__(metrics)
        self._mcp_call = mcp_call
        self._timeout_seconds = timeout_seconds
        self._fallback = fallback
        self._interview = interview
        self._scope = scope

    async def _execute(self) -> tuple[str | None, list[DossierSection]]:
        return await asyncio.wait_for(self._mcp_call(), timeout=self._timeout_seconds)

    def _failure_kind(self) -> FailureKind:
        return FailureKind.DOSSIER_FALLBACK

    def _labels(self) -> dict[str, str]:
        return {"scope": self._scope, "fallback": type(self._fallback).__name__}

    def _log_failure(self, exc: Exception) -> None:
        logger.warning(
            "mcp-server dossier generation failed, falling back to %s",
            type(self._fallback).__name__,
            exc_info=True,
        )

    async def _recover(self, exc: Exception) -> tuple[str | None, list[DossierSection]]:
        return await self._fallback.generate(self._interview, self._scope)


class LLMDossierGenerator(IDossierGenerator):
    """Generates dossier content via mcp-server's `generate_dossier` tool."""

    def __init__(
        self,
        mcp_server_url: str,
        fallback: IDossierGenerator,
        timeout_seconds: float = 45.0,
        metrics: IMetricsPort | None = None,
    ) -> None:
        """Configure the adapter.

        Args:
            mcp_server_url: Base URL of mcp-server's streamable-HTTP endpoint
                (e.g. "http://localhost:8000/mcp").
            fallback: Generator used whenever the mcp-server path fails or the
                timeout elapses.
            timeout_seconds: Wall-clock budget for the whole mcp-server round
                trip (connection, tool call, and the LLM generation it runs).
            metrics: Optional port for recording a fallback to `fallback`. If
                None, the fallback is still logged but not counted (BE-20).
        """
        self._mcp_server_url = mcp_server_url
        self._fallback = fallback
        self._timeout_seconds = timeout_seconds
        self._metrics = metrics

    async def generate(
        self, interview: Interview, scope: DossierScope = "offboarding"
    ) -> tuple[str | None, list[DossierSection]]:
        """Generate dossier content, falling back on any failure.

        Args:
            interview: The completed interview to derive dossier content from.
            scope: Which kind of dossier to write, forwarded to mcp-server's
                'generate_dossier' tool as 'review_scope'.

        Returns:
            A tuple of (summary, sections) to persist on the dossier.
        """
        return await DossierGenerationOperation(
            self._metrics,
            lambda: self._generate_via_mcp(interview, scope),
            self._timeout_seconds,
            self._fallback,
            interview,
            scope,
        ).run()

    async def _generate_via_mcp(
        self, interview: Interview, scope: DossierScope
    ) -> tuple[str | None, list[DossierSection]]:
        async with streamablehttp_client(self._mcp_server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "generate_dossier",
                    {
                        "interview_transcript": _format_interview(interview),
                        "review_scope": scope,
                    },
                )
                text = _tool_result_text(result)
                if result.isError:
                    raise RuntimeError(f"generate_dossier tool call failed: {text}")
                return parse_llm_response(text)


def _tool_result_text(result: Any) -> str:
    parts = [block.text for block in result.content if getattr(block, "type", None) == "text"]
    if not parts:
        raise ValueError("generate_dossier returned no text content")
    return "\n".join(parts)


def _format_interview(interview: Interview) -> str:
    lines: list[str] = []
    for turn in sorted(interview.turns, key=lambda t: t.order):
        if isinstance(turn, InterviewQuestion):
            lines.append(f"Q: {turn.content}")
            lines.append(f"A: {turn.answer_text if turn.answer_text else '(no answer)'}")
        elif isinstance(turn, InterviewNote):
            lines.append(f"Note: {turn.content}")
    transcript = "\n".join(lines) if lines else "(no interview content recorded)"
    return f"Interview transcript:\n\n{transcript}"
