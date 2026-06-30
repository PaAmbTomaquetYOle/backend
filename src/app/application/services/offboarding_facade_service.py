"""Facade service composing the three domain services for use by HTTP routers."""

import logging
from datetime import datetime, timezone

from app.application.ports.event_publisher import IEventPublisher
from app.application.service_interfaces.dossier_service_interface import IDossierService
from app.application.service_interfaces.interview_service_interface import IInterviewService
from app.application.service_interfaces.offboarding_facade_interface import (
    IOffboardingServiceFacade,
)
from app.application.service_interfaces.offboarding_process_service_interface import (
    IOffboardingProcessService,
)
from app.domain import (
    Dossier,
    DossierSection,
    EmployeeId,
    Interview,
    InterviewTurn,
    ManagerId,
    OffboardingProcess,
    OffboardingProcessId,
)
from app.domain.enums import OffboardingProcessStateEnum
from app.domain.events.offboarding_events import (
    DossierGenerated,
    InterviewCompleted,
    OffboardingStateChanged,
)
from app.domain.exceptions.dossier import DossierAlreadyExistsForProcessError

logger = logging.getLogger(__name__)


class OffboardingFacadeService(IOffboardingServiceFacade):
    """Facade composing OffboardingProcessService, InterviewService, and DossierService.

    Implements IOffboardingServiceFacade, providing a single entry point for all
    offboarding operations to the HTTP layer. Coordinates cross-domain validation
    (e.g. verifying process existence before interview or dossier operations) and
    resolves inter-aggregate references (e.g. fetching the interview ID when creating
    a dossier).
    """

    def __init__(
            self,
            process_service: IOffboardingProcessService,
            interview_service: IInterviewService,
            dossier_service: IDossierService,
            event_publisher: IEventPublisher | None = None,
    ) -> None:
        """Set up the facade with the three domain services.

        Args:
            process_service: Service handling offboarding process lifecycle operations.
            interview_service: Service handling interview lifecycle operations.
            dossier_service: Service handling dossier lifecycle operations.
            event_publisher: Optional publisher for domain events. If None, events are not published.
        """
        self._process_service = process_service
        self._interview_service = interview_service
        self._dossier_service = dossier_service
        self._event_publisher = event_publisher

    async def _publish(self, event) -> None:
        """Publish a domain event, logging a warning if publishing fails.

        Args:
            event: The domain event to publish.
        """
        if self._event_publisher is not None:
            try:
                await self._event_publisher.publish(event)
            except Exception:
                logger.warning("Failed to publish event %s", event.event_type, exc_info=True)

    async def create_offboarding(
            self,
            employee_id: EmployeeId,
            manager_id: ManagerId,
    ) -> OffboardingProcess:
        """Create a new offboarding process in NOT_STARTED state.

        Delegates to process_service.create_process.

        Args:
            employee_id: Identifier of the employee being offboarded.
            manager_id: Identifier of the manager responsible for the process.

        Returns:
            The newly created OffboardingProcess.
        """
        return await self._process_service.create_process(employee_id, manager_id)

    async def get_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Retrieve an offboarding process by ID.

        Args:
            process_id: Identifier of the process to retrieve.

        Returns:
            The matching OffboardingProcess.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        return await self._process_service.get_process(process_id)

    async def list_offboardings(
            self,
            employee_id: EmployeeId | None = None,
            manager_id: ManagerId | None = None,
            state: OffboardingProcessStateEnum | None = None,
    ) -> list[OffboardingProcess]:
        """Return offboarding processes matching optional filters.

        Args:
            employee_id: Filter by employee. Defaults to None.
            manager_id: Filter by manager. Defaults to None.
            state: Filter by lifecycle state. Defaults to None.

        Returns:
            List of matching OffboardingProcess objects.
        """
        results = await self._process_service.get_filtered_processes(
            employee_id=employee_id,
            manager_id=manager_id,
            state=state,
        )
        return list(results)

    async def delete_offboarding(self, process_id: OffboardingProcessId) -> None:
        """Delete an offboarding process by ID.

        Args:
            process_id: Identifier of the process to delete.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        await self._process_service.delete_process(process_id)

    async def start_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from NOT_STARTED to IN_PROGRESS.

        Args:
            process_id: Identifier of the process to start.

        Returns:
            The updated OffboardingProcess in IN_PROGRESS state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in NOT_STARTED state.
        """
        process = await self._process_service.start_offboarding(process_id)
        await self._publish(OffboardingStateChanged(
            process_id=process.process_id.get_id(),
            previous_state="not_started",
            new_state="in_progress",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        return process

    async def submit_offboarding_for_review(
            self,
            process_id: OffboardingProcessId
    ) -> OffboardingProcess:
        """Transition the process from IN_PROGRESS to PENDING_REVISION.

        Args:
            process_id: Identifier of the process to submit.

        Returns:
            The updated OffboardingProcess in PENDING_REVISION state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in IN_PROGRESS state.
        """
        process = await self._process_service.submit_for_review(process_id)
        await self._publish(OffboardingStateChanged(
            process_id=process.process_id.get_id(),
            previous_state="in_progress",
            new_state="pending_revision",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        return process

    async def complete_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Transition the process from PENDING_REVISION to FINISHED.

        Args:
            process_id: Identifier of the process to complete.

        Returns:
            The updated OffboardingProcess in FINISHED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is not in PENDING_REVISION state.
        """
        process = await self._process_service.complete_offboarding(process_id)
        await self._publish(OffboardingStateChanged(
            process_id=process.process_id.get_id(),
            previous_state="pending_revision",
            new_state="finished",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        return process

    async def cancel_offboarding(self, process_id: OffboardingProcessId) -> OffboardingProcess:
        """Cancel the offboarding process.

        Args:
            process_id: Identifier of the process to cancel.

        Returns:
            The updated OffboardingProcess in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InvalidOffboardingProcessStateTransitionError: If the process is already in a terminal state.
        """
        process = await self._process_service.cancel_offboarding(process_id)
        await self._publish(OffboardingStateChanged(
            process_id=process.process_id.get_id(),
            previous_state="in_progress",
            new_state="cancelled",
            employee_id=process.employee_id.get_id(),
            manager_id=process.manager_id.get_id(),
        ))
        return process

    async def upsert_interview(
            self,
            process_id: OffboardingProcessId,
            scheduled_at: datetime,
            turns: list[InterviewTurn] | None = None,
    ) -> tuple[Interview, bool]:
        """Create or replace the interview for the given offboarding process.

        First verifies the process exists, then delegates to interview_service.upsert_interview.

        Args:
            process_id: Identifier of the offboarding process.
            scheduled_at: Datetime when the interview is scheduled.
            turns: Optional list of turns to attach. Defaults to None.

        Returns:
            A tuple of (interview, created) where created is True if a new interview
            was created, or False if an existing one was updated.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
        """
        await self._process_service.get_process(process_id)
        return await self._interview_service.upsert_interview(process_id, scheduled_at, turns)

    async def get_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Retrieve the interview associated with the given offboarding process.

        First verifies the process exists, then delegates to interview_service.get_process_interview.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Interview linked to the process.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
        """
        await self._process_service.get_process(process_id)
        return await self._interview_service.get_process_interview(process_id)

    async def start_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Transition the process's interview from SCHEDULED to IN_PROGRESS.

        Resolves the interview for the process, then delegates the transition.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The updated Interview in IN_PROGRESS state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InvalidInterviewStateTransitionError: If the interview is not in SCHEDULED state.
        """
        interview = await self.get_interview(process_id)
        return await self._interview_service.start_interview(interview.interview_id)

    async def complete_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Transition the process's interview from IN_PROGRESS to COMPLETED.

        Resolves the interview for the process, then delegates the transition.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The updated Interview in COMPLETED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InvalidInterviewStateTransitionError: If the interview is not in IN_PROGRESS state.
        """
        interview = await self.get_interview(process_id)
        result = await self._interview_service.complete_interview(interview.interview_id)
        await self._publish(InterviewCompleted(
            interview_id=result.interview_id.get_id(),
            process_id=process_id.get_id(),
            completed_at=datetime.now(timezone.utc).isoformat(),
        ))
        return result

    async def cancel_interview(self, process_id: OffboardingProcessId) -> Interview:
        """Cancel the process's interview.

        Resolves the interview for the process, then delegates the transition.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The updated Interview in CANCELLED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InvalidInterviewStateTransitionError: If the interview is already in a terminal state.
        """
        interview = await self.get_interview(process_id)
        return await self._interview_service.cancel_interview(interview.interview_id)

    async def add_interview_turns(
            self,
            process_id: OffboardingProcessId,
            turns: list[InterviewTurn],
    ) -> Interview:
        """Append turns to the in-progress interview of the given process.

        Resolves the interview for the process, then delegates to interview_service.add_turns.

        Args:
            process_id: Identifier of the offboarding process.
            turns: Ordered list of turns to append to the interview.

        Returns:
            The updated Interview with the new turns appended.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            InterviewNotInProgressError: If the interview is not in IN_PROGRESS state.
            InterviewTurnOrderError: If any turn has an invalid order value.
        """
        interview = await self.get_interview(process_id)
        return await self._interview_service.add_turns(interview.interview_id, turns)

    async def create_dossier(
            self,
            process_id: OffboardingProcessId,
            summary: str | None = None,
            sections: list[DossierSection] | None = None,
    ) -> Dossier:
        """Create a dossier for the given offboarding process.

        Validates that the process exists, retrieves its interview (needed to link the
        dossier), checks no dossier already exists for the process, then delegates
        creation to dossier_service.

        Args:
            process_id: Identifier of the offboarding process.
            summary: Optional free-text summary of the dossier. Defaults to None.
            sections: Optional list of dossier sections. Defaults to None.

        Returns:
            The newly created Dossier in NOT_GENERATED state.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            InterviewNotFoundError: If no interview exists for the given process.
            DossierAlreadyExistsForProcessError: If a dossier already exists for the process.
        """
        await self._process_service.get_process(process_id)
        interview = await self._interview_service.get_process_interview(process_id)
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
        return dossier

    async def get_dossier(self, process_id: OffboardingProcessId) -> Dossier:
        """Retrieve the dossier for the given offboarding process.

        First verifies the process exists, then delegates to dossier_service.

        Args:
            process_id: Identifier of the offboarding process.

        Returns:
            The Dossier linked to the process.

        Raises:
            ProcessNotFoundError: If no process with the given ID exists.
            DossierNotFoundError: If no dossier exists for the given process.
        """
        await self._process_service.get_process(process_id)
        return await self._dossier_service.get_process_dossier(process_id)
