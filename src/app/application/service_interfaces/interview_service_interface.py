from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import Interview, InterviewTurn, ProcessId


class IInterviewService(ABC):
    """
    Interface for all interview services.
    """

    @abstractmethod
    async def create_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None
    ) -> Interview:
        """
        Create an interview.

        Args:
            process_id (ProcessId): The id of the process to associate the interview with.
            scheduled_at (datetime): The scheduled date and time for the interview.
            turns (list[InterviewTurn]): The various interactions of the interview.

        Returns:
            Interview: The created interview.
        """