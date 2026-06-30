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
    InvalidStateTransitionError,
    ProcessNotFoundError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProcessNotFoundError)
    async def process_not_found_handler(request: Request, exc: ProcessNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InterviewNotFoundError)
    async def interview_not_found_handler(request: Request, exc: InterviewNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DossierNotFoundError)
    async def dossier_not_found_handler(request: Request, exc: DossierNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_transition_handler(request: Request, exc: InvalidStateTransitionError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InterviewAlreadyExistsForProcessError)
    async def interview_already_exists_handler(
            request: Request, exc: InterviewAlreadyExistsForProcessError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DossierAlreadyExistsForProcessError)
    async def dossier_already_exists_handler(
            request: Request, exc: DossierAlreadyExistsForProcessError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InterviewNotInProgressError)
    async def interview_not_in_progress_handler(
            request: Request, exc: InterviewNotInProgressError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DossierInterviewNotCompletedError)
    async def dossier_interview_not_completed_handler(
            request: Request, exc: DossierInterviewNotCompletedError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InterviewTurnOrderError)
    async def interview_turn_order_handler(request: Request, exc: InterviewTurnOrderError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DossierSectionError)
    async def dossier_section_handler(request: Request, exc: DossierSectionError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        orig = str(exc.orig) if exc.orig else str(exc)
        return JSONResponse(status_code=409, content={"detail": f"Constraint violation: {orig}"})

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
