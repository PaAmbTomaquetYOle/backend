"""SQLModel-backed repository for interviews."""
from collections.abc import Sequence

from sqlmodel import Session, col, select

from app.application.ports.interview import IInterviewRepository
from app.domain.interview.interview import Interview
from app.domain.offboarding.id import InterviewId, OffboardingProcessId
from app.infrastructure.persistence.models.interview import (
    InterviewModel,
    InterviewTurnModel,
)


class InterviewRepository(IInterviewRepository):
    """SQLModel-backed implementation of IInterviewRepository."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session: The active SQLModel session to use for all queries.
        """
        self._session = session

    def save(self, interview: Interview) -> None:
        """Persist an interview and all its turns (insert or update)."""
        model = InterviewModel.from_domain(interview)
        self._session.merge(model)
        self._session.flush()

        stmt = select(InterviewTurnModel).where(
            col(InterviewTurnModel.interview_id) == model.id
        )
        existing_turns = self._session.exec(stmt).all()
        for turn in existing_turns:
            self._session.delete(turn)
        self._session.flush()

        interview_id = model.id
        for turn in interview.turns:
            turn_model = InterviewTurnModel.from_domain(turn, interview_id)
            self._session.add(turn_model)

        self._session.commit()

    def find_by_id(self, interview_id: InterviewId) -> Interview | None:
        """Return the interview with the given ID, or None if not found."""
        model = self._session.get(InterviewModel, interview_id.get_id())
        if not model:
            return None
        turns: Sequence[InterviewTurnModel] = self._session.exec(
            select(InterviewTurnModel).where(
                col(InterviewTurnModel.interview_id) == model.id
            )
        ).all()
        # noinspection PyTypeChecker
        return model.to_domain(list(turns))

    def find_by_process_id(self, process_id: OffboardingProcessId) -> Interview | None:
        """Return the interview for the given process, or None if not found."""
        model: InterviewModel | None = self._session.exec(
            select(InterviewModel).where(
                col(InterviewModel.process_id) == process_id.get_id()
            )
        ).first()
        if not model:
            return None
        turns: Sequence[InterviewTurnModel] = self._session.exec(
            select(InterviewTurnModel).where(
                col(InterviewTurnModel.interview_id) == model.id
            )
        ).all()
        return model.to_domain(list(turns))

    def find_all(self) -> list[Interview]:
        """Return all stored interviews."""
        models = self._session.exec(select(InterviewModel)).all()
        result: list[Interview] = []
        for model in models:
            turns = self._session.exec(
                select(InterviewTurnModel).where(
                    col(InterviewTurnModel.interview_id) == model.id
                )
            ).all()
            result.append(model.to_domain(list(turns)))
        return result

    def delete(self, interview_id: InterviewId) -> None:
        """Remove the interview with the given ID (no-op if not found)."""
        model = self._session.get(InterviewModel, interview_id.get_id())
        if model:
            self._session.delete(model)
            self._session.commit()
