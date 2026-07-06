"""SOP (Standard Operating Procedure) bounded context.

A SOP is a knowledge document — not a lifecycle process — so it deliberately
does not extend ``Process`` or use the State pattern used by offboarding.
"""

from .id import AuthorId, ChannelId, SopId
from .sop import Sop

__all__ = [
    "AuthorId",
    "ChannelId",
    "Sop",
    "SopId",
]
