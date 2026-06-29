"""Dossier aggregate root."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.enums import InterviewStateEnum
from app.domain.exceptions.dossier import DossierInterviewNotCompletedError

if TYPE_CHECKING:
    from app.domain.dossier.section import DossierSection
    from app.domain.dossier.state.base import DossierState
    from app.domain.offboarding.id import DossierId, InterviewId, OffboardingProcessId


class Dossier:
    """Dossier aggregate root. 1:1 with OffboardingProcess."""

    def __init__(
        self,
        dossier_id: DossierId,
        process_id: OffboardingProcessId,
        interview_id: InterviewId,
        state: DossierState,
        created_at: datetime,
        summary: str | None = None,
        sections: list[DossierSection] | None = None,
    ) -> None:
        self.__id = dossier_id
        self.__process_id = process_id
        self.__interview_id = interview_id
        self.__state = state
        self.__created_at = created_at
        self.__summary = summary
        self.__sections: list[DossierSection] = sections if sections is not None else []

    @property
    def dossier_id(self) -> DossierId:
        return self.__id

    @dossier_id.setter
    def dossier_id(self, dossier_id: DossierId) -> None:
        self.__id = dossier_id

    @property
    def process_id(self) -> OffboardingProcessId:
        return self.__process_id

    @property
    def interview_id(self) -> InterviewId:
        return self.__interview_id

    @property
    def state(self) -> DossierState:
        return self.__state

    @property
    def summary(self) -> str | None:
        return self.__summary

    @summary.setter
    def summary(self, value: str | None) -> None:
        self.__summary = value

    @property
    def sections(self) -> list[DossierSection]:
        return list(self.__sections)

    @property
    def created_at(self) -> datetime:
        return self.__created_at

    def start_generating(self, interview_state: InterviewStateEnum) -> DossierState:
        """
        Begin dossier generation. Enforces that the interview is COMPLETED.

        Args:
            interview_state: The current state enum of the associated interview.

        Returns:
            DossierState: The new state after transitioning to GENERATING.

        Raises:
            DossierInterviewNotCompletedError: If interview is not completed.
            InvalidDossierStateTransitionError: If dossier is not in NOT_GENERATED state.
        """
        if interview_state != InterviewStateEnum.COMPLETED:
            raise DossierInterviewNotCompletedError()
        new_state = self.__state.start_generating()
        self.__state = new_state
        return new_state

    def complete_generation(self) -> DossierState:
        """
        Mark generation as complete, transitioning to DRAFT.

        Returns:
            DossierState: The new state after transitioning to DRAFT.

        Raises:
            InvalidDossierStateTransitionError: If dossier is not in GENERATING state.
        """
        new_state = self.__state.complete_generation()
        self.__state = new_state
        return new_state

    def submit_for_review(self) -> DossierState:
        """
        Submit the dossier for manager review.

        Returns:
            DossierState: The new state after transitioning to UNDER_REVIEW.

        Raises:
            InvalidDossierStateTransitionError: If dossier is not in DRAFT state.
        """
        new_state = self.__state.submit_for_review()
        self.__state = new_state
        return new_state

    def approve(self) -> DossierState:
        """
        Approve the dossier.

        Returns:
            DossierState: The new state after transitioning to APPROVED.

        Raises:
            InvalidDossierStateTransitionError: If dossier is not in UNDER_REVIEW state.
        """
        new_state = self.__state.approve()
        self.__state = new_state
        return new_state

    def cancel(self) -> DossierState:
        """
        Cancel the dossier.

        Returns:
            DossierState: The new state after transitioning to CANCELLED.

        Raises:
            InvalidDossierStateTransitionError: If dossier is in a terminal state.
        """
        new_state = self.__state.cancel()
        self.__state = new_state
        return new_state

    def add_section(self, section: DossierSection) -> None:
        """Append a section to the dossier."""
        self.__sections.append(section)
