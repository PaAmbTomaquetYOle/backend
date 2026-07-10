"""SQLModel persistence model for dossiers."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlmodel import Field, SQLModel

from app.domain.dossier.dossier import Dossier
from app.domain.dossier.section import DossierSection
from app.domain.dossier.state.approved import ApprovedDossierState
from app.domain.dossier.state.base import DossierState
from app.domain.dossier.state.cancelled import CancelledDossierState
from app.domain.dossier.state.draft import DraftDossierState
from app.domain.dossier.state.generating import GeneratingDossierState
from app.domain.dossier.state.not_generated import NotGeneratedDossierState
from app.domain.dossier.state.under_review import UnderReviewDossierState
from app.domain.enums import DossierStateEnum
from app.domain.offboarding.id import DossierId, InterviewId, ProcessId

_DOSSIER_STATE_FACTORIES: dict[str, type[DossierState]] = {
    DossierStateEnum.NOT_GENERATED.value: NotGeneratedDossierState,
    DossierStateEnum.GENERATING.value: GeneratingDossierState,
    DossierStateEnum.DRAFT.value: DraftDossierState,
    DossierStateEnum.UNDER_REVIEW.value: UnderReviewDossierState,
    DossierStateEnum.APPROVED.value: ApprovedDossierState,
    DossierStateEnum.CANCELLED.value: CancelledDossierState,
}


class DossierModel(SQLModel, table=True):
    """SQLModel persistence model for dossiers."""

    __tablename__ = "dossiers"
    __table_args__ = (
        CheckConstraint(
            "state IN ('not_generated','generating','draft','under_review','approved','cancelled')",
            name="ck_dossiers_state",
        ),
    )

    id: uuid.UUID = Field(primary_key=True)
    process_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("processes.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    interview_id: uuid.UUID = Field(
        sa_column=Column(
            sa.Uuid,
            ForeignKey("interviews.id"),
            nullable=False,
            unique=True,
        )
    )
    state: str = Field(nullable=False)
    created_at: datetime = Field(nullable=False)
    summary: str | None = Field(default=None)

    @classmethod
    def from_domain(cls, dossier: Dossier) -> DossierModel:
        """Create a DossierModel from a domain Dossier aggregate.

        Args:
            dossier: The domain Dossier to persist.

        Returns:
            DossierModel: The corresponding persistence model.
        """
        return cls(
            id=dossier.dossier_id.get_id(),
            process_id=dossier.process_id.get_id(),
            interview_id=dossier.interview_id.get_id(),
            state=dossier.state.get_state().value,
            created_at=dossier.created_at,
            summary=dossier.summary,
        )

    def to_domain(self, sections: list[DossierSection] | None = None) -> Dossier:
        """Reconstruct a domain Dossier from this model and its associated section models.

        Args:
            sections: List of domain DossierSection objects. Defaults to None (empty list).

        Returns:
            Dossier: The reconstructed domain aggregate.
        """
        state = _DOSSIER_STATE_FACTORIES[self.state]()
        return Dossier(
            dossier_id=DossierId(self.id),
            process_id=ProcessId(self.process_id),
            interview_id=InterviewId(self.interview_id),
            state=state,
            created_at=self.created_at,
            summary=self.summary,
            sections=sections,
        )
