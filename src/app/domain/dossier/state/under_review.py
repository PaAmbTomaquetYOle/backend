"""UNDER_REVIEW state: dossier has been submitted for manager review."""

from __future__ import annotations

from app.domain.dossier.state.approved import ApprovedDossierState
from app.domain.dossier.state.base import DossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.enums import DossierStateEnum


class UnderReviewDossierState(DossierState):
    """Dossier is under manager review."""

    def get_state(self) -> DossierStateEnum:
        return DossierStateEnum.UNDER_REVIEW

    def approve(self) -> DossierState:
        return ApprovedDossierState()

    def cancel(self) -> DossierState:
        return CancelledDossierState()
