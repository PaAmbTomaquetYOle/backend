"""Concrete implementation of the interview service."""

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
    """Orchestrates interview lifecycle operations. Delegates persistence to IInterviewRepository."""

    def __init__(self, repo: IInterviewRepository) -> None:
        """Set up the service with a repository.

        Args:
            repo: The repository used to persist and retrieve interviews.
        """
        self._repo = repo

    async def create_interview(
            self,
            process_id: ProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> Interview:
        """Create and persist a new interview in SCHEDULED state.

        Args:
            process_id: Identifier of the offboarding process this interview belongs to.
            scheduled_at: Datetime when the interview is scheduled to take place.
            turns: Optional list of pre-existing turns to attach. Defaults to None.

        Returns:
            The newly created and persisted Interview.
        """
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
        """Retrieve an interview by its own ID.

        Args:
            interview_id: Identifier of the interview to retrieve.

        Returns:
            The matching Interview.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
        """
        interview = self._repo.find_by_id(interview_id)
        if interview is None:
            raise InterviewNotFoundError(f"Interview {interview_id.get_id()} not found")
        return interview

    async def get_process_interview(self, process_id: ProcessId) -> Interview:
        """Retrieve the interview associated with the given offboarding process.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Interview linked to the process.

        Raises:
            InterviewNotFoundError: If no interview exists for the given process.
        """
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
        """Create or replace the interview for a process.

        If no interview exists for the process, a new one is created. If one already
        exists, it is replaced: the original interview ID and creation timestamp are
        preserved but scheduled_at and turns are overwritten.

        Args:
            process_id: Identifier of the offboarding process.
            scheduled_at: Datetime when the interview is scheduled.
            turns: Optional list of turns to attach. Defaults to None.

        Returns:
            A tuple of (interview, created) where created is True if a new interview
            was created, or False if an existing one was updated.
        """
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
        """Transition the interview from SCHEDULED to IN_PROGRESS and persist.

        Args:
            interview_id: Identifier of the interview to start.

        Returns:
            The updated Interview in IN_PROGRESS state.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InvalidInterviewStateTransitionError: If the interview is not in SCHEDULED state.
        """
        interview = await self.get_interview(interview_id)
        interview.start()
        self._repo.save(interview)
        return interview

    async def complete_interview(self, interview_id: InterviewId) -> Interview:
        """Transition the interview from IN_PROGRESS to COMPLETED and persist.

        Args:
            interview_id: Identifier of the interview to complete.

        Returns:
            The updated Interview in COMPLETED state.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InvalidInterviewStateTransitionError: If the interview is not in IN_PROGRESS state.
        """
        interview = await self.get_interview(interview_id)
        interview.complete()
        self._repo.save(interview)
        return interview

    async def cancel_interview(self, interview_id: InterviewId) -> Interview:
        """Transition the interview to CANCELLED and persist.

        Args:
            interview_id: Identifier of the interview to cancel.

        Returns:
            The updated Interview in CANCELLED state.

        Raises:
            InterviewNotFoundError: If no interview with the given ID exists.
            InvalidInterviewStateTransitionError: If the interview is already in a terminal state.
        """
        interview = await self.get_interview(interview_id)
        interview.cancel()
        self._repo.save(interview)
        return interview

    async def add_turns(
            self,
            interview_id: InterviewId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to an in-progress interview and persist.

        The interview must be in IN_PROGRESS state. Each turn is validated for correct
        order before being appended.

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
        interview = await self.get_interview(interview_id)
        for turn in turns:
            interview.add_turn(turn)
        self._repo.save(interview)
        return interview
