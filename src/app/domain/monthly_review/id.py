"""Value objects representing typed identifiers used by the monthly review bounded context."""

from __future__ import annotations

from app.domain.offboarding.id import ProcessId


class MonthlyReviewProcessId(ProcessId):
    """
    Class representing a Monthly Review Process ID
    """
