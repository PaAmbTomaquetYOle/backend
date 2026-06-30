from uuid import UUID
from .base import DomainEvent


def OffboardingStateChanged(
    process_id: UUID,
    previous_state: str,
    new_state: str,
    employee_id: UUID,
    manager_id: UUID,
) -> DomainEvent:
    return DomainEvent(
        event_type="offboarding.state_changed",
        payload={
            "process_id": str(process_id),
            "previous_state": previous_state,
            "new_state": new_state,
            "employee_id": str(employee_id),
            "manager_id": str(manager_id),
        },
    )


def InterviewCompleted(
    interview_id: UUID,
    process_id: UUID,
    completed_at: str,
) -> DomainEvent:
    return DomainEvent(
        event_type="interview.completed",
        payload={
            "interview_id": str(interview_id),
            "process_id": str(process_id),
            "completed_at": completed_at,
        },
    )


def DossierGenerated(
    dossier_id: UUID,
    process_id: UUID,
    interview_id: UUID,
) -> DomainEvent:
    return DomainEvent(
        event_type="dossier.generated",
        payload={
            "dossier_id": str(dossier_id),
            "process_id": str(process_id),
            "interview_id": str(interview_id),
        },
    )
