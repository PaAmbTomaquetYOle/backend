from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import Interview, InterviewId, InterviewTurn, ProcessId


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

    @abstractmethod
    async def get_interview(self, interview_id: InterviewId) -> Interview:
        """
        Get an interview.

        Args:
            interview_id (InterviewId): The id of the interview to get.

        Returns:
            Interview: The interview.
        """

    @abstractmethod
    async def get_process_interview(self, process_id: ProcessId) -> Interview:
        """
        Get the interview associated with a process.

        Args:
            process_id (ProcessId): The id of the process to get the interview for.

        Returns:
            Interview: The interview associated with the process.
        """