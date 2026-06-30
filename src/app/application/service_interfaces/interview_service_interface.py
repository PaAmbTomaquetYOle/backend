"""Abstract contract for the interview service."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain import Interview, InterviewId, InterviewTurn, ProcessId


class IInterviewService(ABC):
    """Interface for interview lifecycle management. Implemented by InterviewService."""

    @abstractmethod
    async def create_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None
    ) -> Interview:
        """Create a new interview for the given offboarding process.

        Args:
            process_id: Identifier of the offboarding process this interview belongs to.
            scheduled_at: Datetime when the interview is scheduled to take place.
            turns: Optional list of pre-existing turns to attach. Defaults to None.

        Returns:
            The newly created Interview in SCHEDULED state.
        """

    @abstractmethod
    async def get_interview(self, interview_id: InterviewId) -> Interview:
        """Retrieve an interview by its own ID.

        Args:
            interview_id: Identifier of the interview to retrieve.

        Returns:
            The matching Interview.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
        """

    @abstractmethod
    async def get_process_interview(self, process_id: ProcessId) -> Interview:
        """Retrieve the interview associated with the given offboarding process.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Interview linked to the process.

        Raises:
            InterviewNotFoundError: If no interview exists for the given process.
        """

    @abstractmethod
    async def upsert_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Create or replace the interview for a process.

        If no interview exists for the process, a new one is created. If one already
        exists, it is replaced with the provided data while preserving the original ID
        and creation timestamp.

        Args:
            process_id: Identifier of the offboarding process.
            scheduled_at: Datetime when the interview is scheduled.
            turns: Optional list of turns to attach. Defaults to None.

        Returns:
            A tuple of (interview, created) where created is True if a new interview
            was created, or False if an existing one was updated.
        """

    @abstractmethod
    async def start_interview(self, interview_id: InterviewId) -> Interview:
        """Transition the interview to IN_PROGRESS.

        Args:
            interview_id: Identifier of the interview to start.

        Returns:
            The updated Interview in IN_PROGRESS state.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InvalidInterviewStateTransitionError: If the interview is not in SCHEDULED state.
        """

    @abstractmethod
    async def complete_interview(self, interview_id: InterviewId) -> Interview:
        """Transition the interview to COMPLETED.

        Args:
            interview_id: Identifier of the interview to complete.

        Returns:
            The updated Interview in COMPLETED state.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InvalidInterviewStateTransitionError: If the interview is not in IN_PROGRESS state.
        """

    @abstractmethod
    async def cancel_interview(self, interview_id: InterviewId) -> Interview:
        """Transition the interview to CANCELLED.

        Args:
            interview_id: Identifier of the interview to cancel.

        Returns:
            The updated Interview in CANCELLED state.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InvalidInterviewStateTransitionError: If the interview is already in a terminal state.
        """

    @abstractmethod
    async def add_turns(
            self,
            interview_id: InterviewId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to an in-progress interview.

        Args:
            interview_id: Identifier of the interview to update.
            turns: Ordered list of turns to append.

        Returns:
            The updated Interview with the new turns appended.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InterviewNotInProgressError: If the interview is not in IN_PROGRESS state.
            InterviewTurnOrderError: If any turn has an invalid order value.
        """
