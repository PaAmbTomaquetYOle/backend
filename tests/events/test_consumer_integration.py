"""Integration test — full inbound Kafka consumer cycle with a real DB (SQLite in-memory).

Processes the 3 inbound events end to end through the real facade/services/
repositories (only Kafka I/O and the DomainEvent envelope are out of scope
here — that is covered by test_kafka_consumer.py and test_event_deserializer.py).
Verifies both the resulting domain state and the outbound events published in
response, matching the acceptance criteria: "consumo de cada tipo de evento
con verificación del efecto en el dominio y del evento de respuesta publicado".
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.application.ports.event_publisher import IEventPublisher
from app.application.services.handlers import (
    DossierGenerationRequestedHandler,
    InterviewCompletedHandler,
    OffboardingTriggeredHandler,
    SopCreationRequestedHandler,
)
from app.application.services.inbound_event_dispatcher import InboundEventDispatcher
from app.domain import EmployeeId, OffboardingProcessStateEnum
from app.domain.events.base import DomainEvent
from app.domain.events.inbound_events import (
    DOSSIER_GENERATION_REQUESTED,
    INTERVIEW_COMPLETED,
    OFFBOARDING_TRIGGERED,
    SOP_CREATION_REQUESTED,
)
from app.infrastructure.adapters.ai.fake_dossier_generator import FakeDossierGenerator
from app.infrastructure.composition import build_inbound_context, build_offboarding_facade
from app.infrastructure.persistence import models as _models  # noqa: F401 — registers tables


class _CapturingPublisher(IEventPublisher):
    """Test double that records every published event instead of sending it anywhere."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)

    async def publish_many(self, events: list[DomainEvent]) -> None:
        self.events.extend(events)


def _make_engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.mark.anyio
class TestConsumerIntegration:
    async def test_full_inbound_event_cycle(self) -> None:
        engine = _make_engine()
        publisher = _CapturingPublisher()
        generator = FakeDossierGenerator()
        dispatcher = InboundEventDispatcher([
            OffboardingTriggeredHandler(),
            InterviewCompletedHandler(),
            DossierGenerationRequestedHandler(),
            SopCreationRequestedHandler(),
        ])

        async def dispatch(event: DomainEvent) -> None:
            with Session(engine) as session:
                context = build_inbound_context(session, publisher, generator)
                await dispatcher.dispatch(event, context)

        # 1. offboarding.triggered -> process created and started
        await dispatch(DomainEvent(
            event_type=OFFBOARDING_TRIGGERED,
            payload={"employee_id": "U1", "manager_id": "U2", "employee_name": "Alice"},
            event_id=uuid4(),
        ))

        with Session(engine) as session:
            facade = build_offboarding_facade(session, publisher, generator)
            processes = await facade.list_offboardings(employee_id=EmployeeId("U1"))
        assert len(processes) == 1
        process = processes[0]
        assert process.state_value == OffboardingProcessStateEnum.IN_PROGRESS
        process_id = process.process_id

        # 2. interview.completed -> answers saved, interview completed, process submitted for review
        await dispatch(DomainEvent(
            event_type=INTERVIEW_COMPLETED,
            payload={
                "process_id": str(process_id.get_id()),
                "turns": [{
                    "turn_type": "question",
                    "speaker_role": "interviewer",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "content": "What are your main responsibilities?",
                    "order": 0,
                    "answer_text": "Lead the backend team",
                }],
            },
            event_id=uuid4(),
        ))

        with Session(engine) as session:
            facade = build_offboarding_facade(session, publisher, generator)
            interview = await facade.get_interview(process_id)
            process = await facade.get_offboarding(process_id)
        assert len(interview.turns) == 1
        assert interview.turns[0].answer_text == "Lead the backend team"
        assert process.state_value == OffboardingProcessStateEnum.PENDING_REVISION

        # 3. dossier.generation_requested -> dossier generated and persisted, process finished
        await dispatch(DomainEvent(
            event_type=DOSSIER_GENERATION_REQUESTED,
            payload={"process_id": str(process_id.get_id())},
            event_id=uuid4(),
        ))

        with Session(engine) as session:
            facade = build_offboarding_facade(session, publisher, generator)
            dossier = await facade.get_dossier(process_id)
            process = await facade.get_offboarding(process_id)
        assert dossier.summary is not None
        assert len(dossier.sections) == 1
        assert process.state_value == OffboardingProcessStateEnum.FINISHED

        # 4. sop.creation_requested -> SOP created and persisted
        await dispatch(DomainEvent(
            event_type=SOP_CREATION_REQUESTED,
            payload={
                "content": "How to rotate secrets",
                "author": "U1",
                "origin_channel": "C1",
                "tags": ["security"],
            },
            event_id=uuid4(),
        ))

        with Session(engine) as session:
            sops_service = build_inbound_context(session, publisher, generator).sops
            sops, total = await sops_service.search_sops()
        assert total == 1
        assert sops[0].content == "How to rotate secrets"

        # Response events were published for each step
        published_types = [e.event_type for e in publisher.events]
        assert "offboarding.state_changed" in published_types
        assert "interview.completed" in published_types
        assert "dossier.generated" in published_types
        assert "offboarding.completed" in published_types
        assert "sop.created" in published_types

        SQLModel.metadata.drop_all(engine)
