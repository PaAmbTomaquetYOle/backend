"""Outbound domain events for MonthlyReviewProcess and AnnualReviewProcess.

Parallel to offboarding_events.py's OffboardingStateChanged/OffboardingCompleted,
but with their own event_type namespace so they don't collide with offboarding's
on the wire (BE-23). InterviewCompleted and DossierGenerated remain shared/generic
(see offboarding_events.py) since Interview and Dossier are process-type-agnostic
aggregates already.
"""

from uuid import UUID

from .base import DomainEvent


def MonthlyReviewStateChanged(
    process_id: UUID,
    previous_state: str,
    new_state: str,
    employee_id: str,
    manager_id: str,
) -> DomainEvent:
    return DomainEvent(
        event_type="monthly_review.state_changed",
        payload={
            "process_id": str(process_id),
            "previous_state": previous_state,
            "new_state": new_state,
            "employee_id": str(employee_id),
            "manager_id": str(manager_id),
        },
    )


def MonthlyReviewCompleted(
    process_id: UUID,
    employee_id: str,
    manager_id: str,
    dossier_id: UUID,
) -> DomainEvent:
    return DomainEvent(
        event_type="monthly_review.completed",
        payload={
            "process_id": str(process_id),
            "employee_id": str(employee_id),
            "manager_id": str(manager_id),
            "dossier_id": str(dossier_id),
        },
    )


def AnnualReviewStateChanged(
    process_id: UUID,
    previous_state: str,
    new_state: str,
    employee_id: str,
    manager_id: str,
) -> DomainEvent:
    return DomainEvent(
        event_type="annual_review.state_changed",
        payload={
            "process_id": str(process_id),
            "previous_state": previous_state,
            "new_state": new_state,
            "employee_id": str(employee_id),
            "manager_id": str(manager_id),
        },
    )


def AnnualReviewCompleted(
    process_id: UUID,
    employee_id: str,
    manager_id: str,
    dossier_id: UUID,
) -> DomainEvent:
    return DomainEvent(
        event_type="annual_review.completed",
        payload={
            "process_id": str(process_id),
            "employee_id": str(employee_id),
            "manager_id": str(manager_id),
            "dossier_id": str(dossier_id),
        },
    )
