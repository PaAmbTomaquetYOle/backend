"""Shared API schema types."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response body returned by all error handlers."""

    detail: str
