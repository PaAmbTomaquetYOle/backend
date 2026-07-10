"""Abstract base state for the Dossier state machine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.enums import DossierStateEnum
from app.domain.exceptions import InvalidDossierStateTransitionError


class DossierState(ABC):
    """Abstract base class for dossier states."""

    @abstractmethod
    def get_state(self) -> DossierStateEnum:
        """Returns the current dossier state."""

    def start_generating(self) -> DossierState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidDossierStateTransitionError: Always, since the current state
                does not support starting generation.
        """
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.GENERATING)

    def complete_generation(self) -> DossierState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidDossierStateTransitionError: Always, since the current state
                does not support completing generation.
        """
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.DRAFT)

    def submit_for_review(self) -> DossierState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidDossierStateTransitionError: Always, since the current state
                does not support submitting for review.
        """
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.UNDER_REVIEW)

    def approve(self) -> DossierState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidDossierStateTransitionError: Always, since the current state
                does not support approval.
        """
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.APPROVED)

    def cancel(self) -> DossierState:
        """Raise an error — this transition is not valid from the current state.

        Raises:
            InvalidDossierStateTransitionError: Always, since the current state
                does not support cancellation.
        """
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.CANCELLED)
