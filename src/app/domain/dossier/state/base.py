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
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.GENERATING)

    def complete_generation(self) -> DossierState:
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.DRAFT)

    def submit_for_review(self) -> DossierState:
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.UNDER_REVIEW)

    def approve(self) -> DossierState:
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.APPROVED)

    def cancel(self) -> DossierState:
        raise InvalidDossierStateTransitionError(self.get_state(), DossierStateEnum.CANCELLED)
