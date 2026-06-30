from datetime import UTC, datetime

from app.application.ports.interview import IInterviewRepository
from app.application.service_interfaces.interview_service_interface import IInterviewService
from app.domain import (
    Interview,
    InterviewId,
    InterviewTurn,
    ProcessId,
    ScheduledInterviewState,
)
from app.domain.exceptions.interview import InterviewNotFoundError


class InterviewService(IInterviewService):

    def __init__(self, repo: IInterviewRepository) -> None:
        self._repo = repo

    async def create_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> Interview:
        interview = Interview(
            interview_id=InterviewId(),
            process_id=process_id,
            state=ScheduledInterviewState(),
            scheduled_at=scheduled_at,
            created_at=datetime.now(UTC),
            turns=turns,
        )
        self._repo.save(interview)
        return interview

    async def get_interview(self, interview_id: InterviewId) -> Interview:
        interview = self._repo.find_by_id(interview_id)
        if interview is None:
            raise InterviewNotFoundError(f"Interview {interview_id.get_id()} not found")
        return interview

    async def get_process_interview(self, process_id: ProcessId) -> Interview:
        interview = self._repo.find_by_process_id(process_id)
        if interview is None:
            raise InterviewNotFoundError(f"No interview found for process {process_id.get_id()}")
        return interview

    async def upsert_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Returns (interview, created) where created=True if newly created."""
        existing = self._repo.find_by_process_id(process_id)
        if existing is None:
            interview = await self.create_interview(process_id, scheduled_at, turns)
            return interview, True
        updated = Interview(
            interview_id=existing.interview_id,
            process_id=process_id,
            state=existing.state,
            scheduled_at=scheduled_at,
            created_at=existing.created_at,
            turns=turns,
        )
        self._repo.save(updated)
        return updated, False

    async def start_interview(self, interview_id: InterviewId) -> Interview:
        interview = await self.get_interview(interview_id)
        interview.start()
        self._repo.save(interview)
        return interview

    async def complete_interview(self, interview_id: InterviewId) -> Interview:
        interview = await self.get_interview(interview_id)
        interview.complete()
        self._repo.save(interview)
        return interview

    async def cancel_interview(self, interview_id: InterviewId) -> Interview:
        interview = await self.get_interview(interview_id)
        interview.cancel()
        self._repo.save(interview)
        return interview

    async def add_turns(
            self,
            interview_id: InterviewId,
            turns: list[InterviewTurn],
    ) -> Interview:
        interview = await self.get_interview(interview_id)
        for turn in turns:
            interview.add_turn(turn)
        self._repo.save(interview)
        return interview
