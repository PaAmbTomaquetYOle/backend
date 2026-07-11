"""Handles the inbound 'tasks.extracted' event (SA-18)."""

from app.application.ports.inbound_event_handler import IInboundEventHandler
from app.application.services.inbound_context import InboundContext
from app.domain.enums import TaskSourceEnum
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import TASKS_EXTRACTED
from app.domain.offboarding.id import OffboardingProcessId
from app.domain.offboarding.task import OffboardingTask


class OffboardingTasksExtractedHandler(IInboundEventHandler):
    """Persists the full set of Jira/Trello tasks extracted for an offboarding process.

    Expected payload: process_id, tasks (each with id, title, source, status, and optionally
    url/description). Replaces whatever was previously stored for the process (SA-18) — tasks
    are extracted once per interview and re-extraction always carries the current full set.
    """

    @property
    def event_type(self) -> str:
        """The event_type this handler is responsible for."""
        return TASKS_EXTRACTED

    async def handle(self, event: DomainEvent, context: InboundContext) -> None:
        """Record the extracted tasks via the offboarding task service.

        Args:
            event: The inbound 'tasks.extracted' event.
            context: Per-message context providing the offboarding task service.
        """
        payload = event.payload
        process_id = OffboardingProcessId(payload["process_id"])
        tasks = [
            OffboardingTask(
                process_id=process_id,
                task_id=raw["id"],
                title=raw["title"],
                source=TaskSourceEnum(raw["source"]),
                status=raw["status"],
                url=raw.get("url"),
                description=raw.get("description"),
            )
            for raw in payload["tasks"]
        ]
        await context.tasks.record_extracted_tasks(process_id, tasks)
