from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import Interview, InterviewId, InterviewTurn, ProcessId


class IInterviewService(ABC):

    @abstractmethod
    async def create_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None
    ) -> Interview: ...

    @abstractmethod
    async def get_interview(self, interview_id: InterviewId) -> Interview: ...

    @abstractmethod
    async def get_process_interview(self, process_id: ProcessId) -> Interview: ...

    @abstractmethod
    async def upsert_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]: ...

    @abstractmethod
    async def start_interview(self, interview_id: InterviewId) -> Interview: ...

    @abstractmethod
    async def complete_interview(self, interview_id: InterviewId) -> Interview: ...

    @abstractmethod
    async def cancel_interview(self, interview_id: InterviewId) -> Interview: ...

    @abstractmethod
    async def add_turns(
            self,
            interview_id: InterviewId,
            turns: list[InterviewTurn],
    ) -> Interview: ...
