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
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.application.ports.dossier_generator import IDossierGenerator
from app.domain.dossier.section import DossierSection
from app.domain.interview.interview import Interview
from app.domain.interview.turn import InterviewNote, InterviewQuestion
from app.infrastructure.adapters.ai.dossier_response_parser import parse_llm_response

logger = logging.getLogger(__name__)


class LLMDossierGenerator(IDossierGenerator):
    """Generates dossier content via mcp-server's `generate_dossier` tool."""

    def __init__(
        self,
        mcp_server_url: str,
        fallback: IDossierGenerator,
        timeout_seconds: float = 45.0,
    ) -> None:
        """Configure the adapter.

        Args:
            mcp_server_url: Base URL of mcp-server's streamable-HTTP endpoint
                (e.g. "http://localhost:8000/mcp").
            fallback: Generator used whenever the mcp-server path fails or the
                timeout elapses.
            timeout_seconds: Wall-clock budget for the whole mcp-server round
                trip (connection, tool call, and the LLM generation it runs).
        """
        self._mcp_server_url = mcp_server_url
        self._fallback = fallback
        self._timeout_seconds = timeout_seconds

    async def generate(self, interview: Interview) -> tuple[str | None, list[DossierSection]]:
        """Generate dossier content, falling back on any failure.

        Args:
            interview: The completed interview to derive dossier content from.

        Returns:
            A tuple of (summary, sections) to persist on the dossier.
        """
        try:
            return await asyncio.wait_for(
                self._generate_via_mcp(interview), timeout=self._timeout_seconds
            )
        except Exception:
            logger.warning(
                "mcp-server dossier generation failed, falling back to %s",
                type(self._fallback).__name__,
                exc_info=True,
            )
            return await self._fallback.generate(interview)

    async def _generate_via_mcp(
        self, interview: Interview
    ) -> tuple[str | None, list[DossierSection]]:
        async with streamablehttp_client(self._mcp_server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "generate_dossier",
                    {"interview_transcript": _format_interview(interview)},
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
