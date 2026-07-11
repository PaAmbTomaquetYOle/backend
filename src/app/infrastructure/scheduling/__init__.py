"""In-process scheduling infrastructure (BE-24).

See ``review_scheduler.py`` for the approach decision and rationale.
"""

from .review_scheduler import ReviewScheduler

__all__: list[str] = ["ReviewScheduler"]
