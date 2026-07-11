"""Tests for OffboardingTasksExtractedHandler (SA-18)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.service_interfaces.offboarding_task_service_interface import (
    IOffboardingTaskService,
)
from app.application.services.handlers.offboarding_tasks_extracted_handler import (
    OffboardingTasksExtractedHandler,
)
from app.application.services.inbound_context import InboundContext
from app.domain.enums import TaskSourceEnum
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import TASKS_EXTRACTED


class TestOffboardingTasksExtractedHandler:
    def test_event_type(self) -> None:
        assert OffboardingTasksExtractedHandler().event_type == TASKS_EXTRACTED

    @pytest.mark.anyio
    async def test_handle_records_the_extracted_tasks(self) -> None:
        tasks_service = AsyncMock(spec=IOffboardingTaskService)
        process_id = str(uuid4())
        event = DomainEvent(
            event_type=TASKS_EXTRACTED,
            payload={
                "process_id": process_id,
                "tasks": [
                    {
                        "id": "PROJ-1",
                        "title": "Fix the thing",
                        "source": "jira",
                        "status": "in_progress",
                        "url": "https://jira/PROJ-1",
                        "description": "desc",
                    },
                    {
                        "id": "T-1",
                        "title": "Card",
                        "source": "trello",
                        "status": "pending",
                    },
                ],
            },
            event_id=uuid4(),
        )
        context = InboundContext(
            offboarding=AsyncMock(),
            monthly_review=AsyncMock(),
            annual_review=AsyncMock(),
            sops=AsyncMock(),
            sop_candidates=AsyncMock(),
            tasks=tasks_service,
            knowledge_graph=AsyncMock(),
        )

        await OffboardingTasksExtractedHandler().handle(event, context)

        tasks_service.record_extracted_tasks.assert_awaited_once()
        (called_process_id, called_tasks), _ = tasks_service.record_extracted_tasks.call_args
        assert called_process_id.get_id() == process_id
        assert len(called_tasks) == 2
        assert called_tasks[0].task_id == "PROJ-1"
        assert called_tasks[0].source == TaskSourceEnum.JIRA
        assert called_tasks[0].url == "https://jira/PROJ-1"
        assert called_tasks[1].task_id == "T-1"
        assert called_tasks[1].source == TaskSourceEnum.TRELLO
        assert called_tasks[1].url is None
