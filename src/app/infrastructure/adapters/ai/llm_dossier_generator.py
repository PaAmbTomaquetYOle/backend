"""LLM-backed, agentic implementation of IDossierGenerator.

Instead of embedding the model-calling logic as an isolated single-shot
completion, this adapter acts as an MCP *client* of ``mcp-server`` (the same
tool surface ``slack-agent`` drives during the interview) so the model can
pull extra context before writing the dossier: prior dossiers for the same
employee/role (``get_dossier``) and relevant SOPs (``test_search_query``).
Only read-only, tokenless tools are exposed here — the Jira/Trello/Slack
tools require a per-user OAuth session that has no meaning for a headless
Kafka consumer.

Flow per ``generate()`` call:
1. Connect to mcp-server over streamable HTTP, open an MCP session.
2. Give the model the interview transcript plus the allow-listed tools.
3. Loop: if the model asks for a tool call, execute it via the MCP session
   and feed the result back; once it answers with plain text, treat that as
   the final JSON dossier payload (see ``dossier_response_parser``).
4. Any failure (connection, timeout, malformed JSON, exhausted tool-call
   budget) is caught and delegated to the configured fallback generator, so a
   flaky LLM/mcp-server never breaks the Kafka consumer's flow.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from anthropic import AsyncAnthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.application.ports.dossier_generator import IDossierGenerator
from app.domain.dossier.section import DossierSection
from app.domain.interview.interview import Interview
from app.domain.interview.turn import InterviewNote, InterviewQuestion
from app.infrastructure.adapters.ai.dossier_response_parser import parse_llm_response

logger = logging.getLogger(__name__)

ALLOWED_TOOLS = frozenset({"get_dossier", "test_search_query"})

SYSTEM_PROMPT = """You write offboarding handover dossiers for departing employees.

You receive an interview transcript (questions and answers, plus any free-form
notes) with a departing employee. Optionally, use the available tools to pull
extra context: `get_dossier` to look up prior dossiers (e.g. for the same
employee's earlier processes, or to see how similar roles were documented),
and `test_search_query` to search the organization's SOP index for knowledge
that relates to topics mentioned in the interview. Use tools only when they
would materially improve the dossier; it's fine to answer without using any.

When you are done, respond with ONLY a single JSON object (no prose, no
markdown fences) with this exact shape:

{
  "summary": "<one paragraph summarizing the handover, or null>",
  "sections": [
    {"type": "responsibilities", "title": "<title>", "responsibilities": ["<string>", ...]},
    {"type": "contacts", "title": "<title>", "contacts": [
        {"name": "<string>", "role": "<string>", "email": "<string>", "relationship": "<string>"}
    ]},
    {"type": "pending_tasks", "title": "<title>", "tasks": [
        {"description": "<string>", "priority": "<low|medium|high>", "deadline": "<string or null>"}
    ]},
    {"type": "knowledge_areas", "title": "<title>", "areas": [
        {"topic": "<string>", "description": "<string>", "expertise_level": "<string>"}
    ]}
  ]
}

Omit section types that don't apply given the interview content. Only include
information actually grounded in the transcript or tool results — never
invent contacts, tasks, or knowledge areas."""


class LLMDossierGenerator(IDossierGenerator):
    """Generates dossier content by driving an LLM with mcp-server tools."""

    def __init__(
        self,
        anthropic_api_key: str,
        model: str,
        mcp_server_url: str,
        fallback: IDossierGenerator,
        timeout_seconds: float = 45.0,
        max_tool_iterations: int = 4,
        max_tokens: int = 4096,
    ) -> None:
        """Configure the adapter.

        Args:
            anthropic_api_key: API key for the Anthropic client.
            model: Anthropic model id to use (e.g. "claude-sonnet-4-5-20250929").
            mcp_server_url: Base URL of mcp-server's streamable-HTTP endpoint
                (e.g. "http://localhost:8000/mcp").
            fallback: Generator used whenever the LLM/mcp-server path fails
                or the timeout elapses.
            timeout_seconds: Wall-clock budget for the whole mcp-server +
                LLM round trip (connection, tool calls, completions included).
            max_tool_iterations: Maximum number of tool-call round trips before
                giving up and falling back.
            max_tokens: Max tokens per Anthropic completion.
        """
        self._client = AsyncAnthropic(api_key=anthropic_api_key)
        self._model = model
        self._mcp_server_url = mcp_server_url
        self._fallback = fallback
        self._timeout_seconds = timeout_seconds
        self._max_tool_iterations = max_tool_iterations
        self._max_tokens = max_tokens

    async def generate(self, interview: Interview) -> tuple[str | None, list[DossierSection]]:
        """Generate dossier content, falling back on any failure.

        Args:
            interview: The completed interview to derive dossier content from.

        Returns:
            A tuple of (summary, sections) to persist on the dossier.
        """
        try:
            return await asyncio.wait_for(
                self._generate_with_llm(interview), timeout=self._timeout_seconds
            )
        except Exception:
            logger.warning(
                "LLM dossier generation failed, falling back to %s",
                type(self._fallback).__name__,
                exc_info=True,
            )
            return await self._fallback.generate(interview)

    async def _generate_with_llm(
        self, interview: Interview
    ) -> tuple[str | None, list[DossierSection]]:
        async with streamablehttp_client(self._mcp_server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await self._list_allowed_tools(session)
                text = await self._run_agent_loop(session, tools, interview)
                return parse_llm_response(text)

    async def _list_allowed_tools(self, session: ClientSession) -> list[dict[str, Any]]:
        listed = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in listed.tools
            if tool.name in ALLOWED_TOOLS
        ]

    async def _run_agent_loop(
        self,
        session: ClientSession,
        tools: list[dict[str, Any]],
        interview: Interview,
    ) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": _format_interview(interview)}]

        for _ in range(self._max_tool_iterations):
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                return _extract_text(response)

            messages.append(
                {"role": "assistant", "content": [block.model_dump() for block in response.content]}
            )
            messages.append(
                {"role": "user", "content": await self._execute_tool_calls(session, response)}
            )

        raise RuntimeError(
            "LLM did not produce a final answer within "
            f"{self._max_tool_iterations} tool-call round trips"
        )

    async def _execute_tool_calls(
        self, session: ClientSession, response: Any
    ) -> list[dict[str, Any]]:
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = await session.call_tool(block.name, block.input)
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": _tool_result_text(result),
                    "is_error": result.isError,
                }
            )
        return results


def _tool_result_text(result: Any) -> str:
    parts = [block.text for block in result.content if getattr(block, "type", None) == "text"]
    return "\n".join(parts) if parts else "(empty tool result)"


def _extract_text(response: Any) -> str:
    parts = [block.text for block in response.content if block.type == "text"]
    if not parts:
        raise ValueError("LLM response contained no text content")
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
