"""Request/response schemas for offboarding task endpoints (SA-18)."""

from pydantic import BaseModel

from app.domain import OffboardingTask


class OffboardingTaskResponse(BaseModel):
    """Response body representing a single extracted Jira/Trello task."""

    id: str
    title: str
    source: str
    status: str
    url: str | None
    description: str | None


class OffboardingTaskListResponse(BaseModel):
    """Response body wrapping the tasks extracted for an offboarding process."""

    items: list[OffboardingTaskResponse]


def task_to_response(task: OffboardingTask) -> OffboardingTaskResponse:
    """Convert a domain OffboardingTask to its API response schema.

    Args:
        task: The domain aggregate to serialize.

    Returns:
        OffboardingTaskResponse: The corresponding response schema.
    """
    return OffboardingTaskResponse(
        id=task.task_id,
        title=task.title,
        source=task.source.value,
        status=task.status,
        url=task.url,
        description=task.description,
    )
