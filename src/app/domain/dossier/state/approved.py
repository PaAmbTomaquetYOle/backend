"""APPROVED state: dossier has been approved. Terminal state."""

from __future__ import annotations

from app.domain.dossier.state.base import DossierState
from app.domain.enums import DossierStateEnum


class ApprovedDossierState(DossierState):
    """Dossier has been approved. Terminal state."""

    def get_state(self) -> DossierStateEnum:
        return DossierStateEnum.APPROVED
