"""Facade service composing the three domain services for monthly review processes."""

import logging
from datetime import datetime, timezone

from app.application.ports.dossier_generator import IDossierGenerator
from app.application.ports.event_publisher import IEventPublisher
from app.application.service_interfaces.dossier_service_interface import IDossierService
from app.application.service_interfaces.interview_service_interface import IInterviewService
from app.application.service_interfaces.monthly_review_facade_interface import (
    IMonthlyReviewServiceFacade,
)
from app.application.service_interfaces.monthly_review_process_service_interface import (
    IMonthlyReviewProcessService,
)
from app.domain import (
    Dossier,
    EmployeeId,
    Interview,
    InterviewTurn,
    ManagerId,
    MonthlyReviewProcess,
    MonthlyReviewProcessId,
    MonthlyReviewProcessStateEnum,
)
from app.domain.events.offboarding_events import DossierGenerated, InterviewCompleted
from app.domain.events.review_events import MonthlyReviewCompleted, MonthlyReviewStateChanged
from app.domain.exceptions.dossier import DossierAlreadyExistsForProcessError

logger = logging.getLogger(__name__)


class MonthlyReviewFacadeService(IMonthlyReviewServiceFacade):
    """Facade composing MonthlyReviewProcessService, InterviewService, and DossierService.

    Mirrors OffboardingFacadeService, but MonthlyReviewProcess has no
    PENDING_REVISION state: completing the interview does not submit the
    process anywhere — dossier generation is what completes it directly
    (IN_PROGRESS -> FINISHED).
    """

    def __init__(
            self,
            process_service: IMonthlyReviewProcessService,
            interview_service: IInterviewService,
            dossier_service: IDossierService,
            event_publisher: IEventPublisher | None = None,
            dossier_generator: IDossierGenerator | None = None,
    ) -> None:
        self._process_service = process_service
        self._interview_service = interview_service
        self._dossier_service = dossier_service
        self._event_publisher = event_publisher
        self._dossier_generator = dossier_generator

    async def _publish(self, event) -> None:
        if self._event_publisher is not None:
            try:
                await self._event_publisher.publish(event)
            except Exception:
                logger.warning("Failed to publish event %s", event.event_type, exc_info=True)

    async def create_review(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            employee_name: str | None = None,
            manager_name: str | None = None,
    ) -> MonthlyReviewProcess:
        """Create a new monthly review process in NOT_STARTED state."""
        return await self._process_service.create_process(
            employee_id, manager_id, employee_name, manager_name
        )

    async def get_review(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess:
        """Retrieve a monthly review process by ID."""
        return await self._process_service.get_process(process_id)

    async def list_reviews(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: MonthlyReviewProcessStateEnum | None = None,
    ) -> list[MonthlyReviewProcess]:
        """Return monthly review processes matching optional filters."""
        results = await self._process_service.get_filtered_processes(
            employee_id=employee_id, manager_id=manager_id, state=state,
        )
        return list(results)

    async def delete_review(self, process_id: MonthlyReviewProcessId) -> None:
        """Delete a monthly review process by ID."""
        await self._process_service.delete_process(process_id)

    async def start_review(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS."""
        process = await self._process_service.start_review(process_id)
        await self._publish(MonthlyReviewStateChanged(
            process_id=process.process_id.get_id(),
            previous_state="not_started",
            new_state="in_progress",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        return process

    async def cancel_review(self, process_id: MonthlyReviewProcessId) -> MonthlyReviewProcess:
        """Cancel the monthly review process."""
        previous_process = await self._process_service.get_process(process_id)
        previous_state = previous_process.state_value.value
        process = await self._process_service.cancel_review(process_id)
        await self._publish(MonthlyReviewStateChanged(
            process_id=process.process_id.get_id(),
            previous_state=previous_state,
            new_state="cancelled",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        return process

    async def upsert_interview(
            self,
            process_id: MonthlyReviewProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Create or replace the interview for the given monthly review process."""
        await self._process_service.get_process(process_id)
        return await self._interview_service.upsert_interview(process_id, scheduled_at, turns)

    async def get_interview(self, process_id: MonthlyReviewProcessId) -> Interview:
        """Retrieve the interview associated with the given monthly review process."""
        await self._process_service.get_process(process_id)
        return await self._interview_service.get_process_interview(process_id)

    async def start_interview(self, process_id: MonthlyReviewProcessId) -> Interview:
        """Transition the process's interview from SCHEDULED to IN_PROGRESS."""
        interview = await self.get_interview(process_id)
        return await self._interview_service.start_interview(interview.interview_id)

    async def complete_interview(self, process_id: MonthlyReviewProcessId) -> Interview:
        """Transition the process's interview from IN_PROGRESS to COMPLETED."""
        interview = await self.get_interview(process_id)
        result = await self._interview_service.complete_interview(interview.interview_id)
        await self._publish(InterviewCompleted(
            interview_id=result.interview_id.get_id(),
            process_id=process_id.get_id(),
            completed_at=datetime.now(timezone.utc).isoformat(),
        ))
        return result

    async def add_interview_turns(
            self,
            process_id: MonthlyReviewProcessId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to the in-progress interview of the given process."""
        interview = await self.get_interview(process_id)
        return await self._interview_service.add_turns(interview.interview_id, turns)

    async def get_dossier(self, process_id: MonthlyReviewProcessId) -> Dossier:
        """Retrieve the dossier for the given monthly review process."""
        await self._process_service.get_process(process_id)
        return await self._dossier_service.get_process_dossier(process_id)

    async def generate_dossier(self, process_id: MonthlyReviewProcessId) -> Dossier:
        """Generate and persist the dossier for a process, then complete it.

        Reads the process's completed interview, generates dossier content,
        persists the dossier (publishing DossierGenerated), advances it to
        DRAFT, completes the monthly review process (IN_PROGRESS -> FINISHED
        directly, no PENDING_REVISION), and publishes MonthlyReviewCompleted.
        """
        interview = await self._interview_service.get_process_interview(process_id)
        if self._dossier_generator is not None:
            summary, sections = await self._dossier_generator.generate(interview, "monthly")
        else:
            summary, sections = None, []

        existing = None
        try:
            existing = await self._dossier_service.get_process_dossier(process_id)
        except Exception:
            pass
        if existing is not None:
            raise DossierAlreadyExistsForProcessError(str(process_id.get_id()))

        dossier = await self._dossier_service.create_dossier(
            process_id=process_id,
            interview_id=interview.interview_id,
            summary=summary,
            sections=sections,
        )
        await self._publish(DossierGenerated(
            dossier_id=dossier.dossier_id.get_id(),
            process_id=process_id.get_id(),
            interview_id=interview.interview_id.get_id(),
        ))
        dossier = await self._dossier_service.advance_generation(
            dossier.dossier_id, interview.state.get_state()
        )

        previous_process = await self._process_service.get_process(process_id)
        previous_state = previous_process.state_value.value
        process = await self._process_service.complete_review(process_id)
        await self._publish(MonthlyReviewStateChanged(
            process_id=process.process_id.get_id(),
            previous_state=previous_state,
            new_state="finished",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        await self._publish(MonthlyReviewCompleted(
            process_id=process.process_id.get_id(),
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
            dossier_id=dossier.dossier_id.get_id(),
        ))
        return dossier
