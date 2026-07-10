"""Tests for domain event classes."""
from uuid import uuid4

import pytest

from app.domain.events.offboarding_events import (
    DossierGenerated,
    InterviewCompleted,
    OffboardingStateChanged,
)


class TestDomainEvent:
    def test_to_dict_structure(self) -> None:
        event = OffboardingStateChanged(
            process_id=uuid4(),
            previous_state="not_started",
            new_state="in_progress",
            employee_id=uuid4(),
            manager_id=uuid4(),
        )
        d = event.to_dict()
        assert d["event_type"] == "offboarding.state_changed"
        assert "event_id" in d
        assert "occurred_at" in d
        assert "payload" in d
        assert d["payload"]["previous_state"] == "not_started"

    def test_interview_completed_event(self) -> None:
        event = InterviewCompleted(
            interview_id=uuid4(),
            process_id=uuid4(),
            completed_at="2026-01-01T00:00:00Z",
        )
        assert event.event_type == "interview.completed"
        assert "interview_id" in event.payload

    def test_dossier_generated_event(self) -> None:
        event = DossierGenerated(
            dossier_id=uuid4(),
            process_id=uuid4(),
            interview_id=uuid4(),
        )
        assert event.event_type == "dossier.generated"
        assert "dossier_id" in event.payload

    def test_offboarding_state_changed_payload(self) -> None:
        process_id = uuid4()
        employee_id = uuid4()
        manager_id = uuid4()
        event = OffboardingStateChanged(
            process_id=process_id,
            previous_state="not_started",
            new_state="in_progress",
            employee_id=employee_id,
            manager_id=manager_id,
        )
        assert event.payload["process_id"] == str(process_id)
        assert event.payload["employee_id"] == str(employee_id)
        assert event.payload["manager_id"] == str(manager_id)
        assert event.payload["new_state"] == "in_progress"

    def test_domain_event_is_frozen_dataclass(self) -> None:
        event = DossierGenerated(
            dossier_id=uuid4(),
            process_id=uuid4(),
            interview_id=uuid4(),
        )
        with pytest.raises((AttributeError, TypeError)):
            event.event_type = "something-else"  # type: ignore[misc]
