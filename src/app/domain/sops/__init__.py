"""SOP (Standard Operating Procedure) bounded context.

A SOP is a knowledge document — not a lifecycle process — so it deliberately
does not extend ``Process`` or use the State pattern used by offboarding.
"""

from .candidate import SopCandidate
from .id import AuthorId, ChannelId, SopCandidateId, SopId
from .sop import Sop

__all__ = [
    "AuthorId",
    "ChannelId",
    "Sop",
    "SopCandidate",
    "SopCandidateId",
    "SopId",
]
