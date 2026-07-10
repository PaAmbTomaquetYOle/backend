"""FastAPI exception handlers mapping domain exceptions to HTTP error responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.domain.exceptions import (
    DomainException,
    DossierAlreadyExistsForProcessError,
    DossierInterviewNotCompletedError,
    DossierNotFoundError,
    DossierSectionError,
    InterviewAlreadyExistsForProcessError,
    InterviewNotFoundError,
    InterviewNotInProgressError,
    InterviewTurnOrderError,
    InvalidCredentialsError,
    InvalidStateTransitionError,
    PersonNotFoundInGraphError,
    ProcessNotFoundError,
    SopNotFoundError,
)


def register_error_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers on the FastAPI application.

    Each handler maps a specific domain exception to an appropriate HTTP status
    code and JSON error body.

    Args:
        app: The FastAPI application instance to register handlers on.
    """

    @app.exception_handler(ProcessNotFoundError)
    async def process_not_found_handler(
            request: Request, exc: ProcessNotFoundError
    ) -> JSONResponse:
        """Return 404 when a ProcessNotFoundError is raised."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InterviewNotFoundError)
    async def interview_not_found_handler(
            request: Request, exc: InterviewNotFoundError
    ) -> JSONResponse:
        """Return 404 when an InterviewNotFoundError is raised."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DossierNotFoundError)
    async def dossier_not_found_handler(
            request: Request, exc: DossierNotFoundError
    ) -> JSONResponse:
        """Return 404 when a DossierNotFoundError is raised."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(SopNotFoundError)
    async def sop_not_found_handler(request: Request, exc: SopNotFoundError) -> JSONResponse:
        """Return 404 when a SopNotFoundError is raised."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PersonNotFoundInGraphError)
    async def person_not_found_in_graph_handler(
            request: Request, exc: PersonNotFoundInGraphError
    ) -> JSONResponse:
        """Return 404 when a PersonNotFoundInGraphError is raised."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_transition_handler(
            request: Request, exc: InvalidStateTransitionError
    ) -> JSONResponse:
        """Return 409 when an invalid state machine transition is attempted."""
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InterviewAlreadyExistsForProcessError)
    async def interview_already_exists_handler(
            request: Request, exc: InterviewAlreadyExistsForProcessError
    ) -> JSONResponse:
        """Return 409 when an interview already exists for a process."""
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DossierAlreadyExistsForProcessError)
    async def dossier_already_exists_handler(
            request: Request, exc: DossierAlreadyExistsForProcessError
    ) -> JSONResponse:
        """Return 409 when a dossier already exists for a process."""
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InterviewNotInProgressError)
    async def interview_not_in_progress_handler(
            request: Request, exc: InterviewNotInProgressError
    ) -> JSONResponse:
        """Return 422 when turns are added to an interview not in progress."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DossierInterviewNotCompletedError)
    async def dossier_interview_not_completed_handler(
            request: Request, exc: DossierInterviewNotCompletedError
    ) -> JSONResponse:
        """Return 422 when a dossier is created before its interview is completed."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InterviewTurnOrderError)
    async def interview_turn_order_handler(
            request: Request, exc: InterviewTurnOrderError
    ) -> JSONResponse:
        """Return 422 when turns are provided in an invalid order."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DossierSectionError)
    async def dossier_section_handler(request: Request, exc: DossierSectionError) -> JSONResponse:
        """Return 422 when a dossier section contains invalid data."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
            request: Request, exc: InvalidCredentialsError
    ) -> JSONResponse:
        """Return 401 when client-credentials verification fails."""
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        """Return 409 when a database integrity constraint is violated."""
        orig = str(exc.orig) if exc.orig else str(exc)
        return JSONResponse(status_code=409, content={"detail": f"Constraint violation: {orig}"})

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        """Return 400 for any unhandled domain exception."""
        return JSONResponse(status_code=400, content={"detail": str(exc)})
