"""Value objects representing typed identifiers used by the annual review bounded context."""

from __future__ import annotations

from app.domain.offboarding.id import ProcessId


class AnnualReviewProcessId(ProcessId):
    """
    Class representing an Annual Review Process ID
    """
