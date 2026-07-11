"""Lifecycle states of a SOP candidate awaiting a Slack accept/reject decision."""

from enum import Enum


class SopCandidateStatus(str, Enum):
    """Status of a SopCandidate.

    A candidate is only ever persisted once it has been offered to its
    author (SA-16) — the pre-offer "tracked but not yet offered" phase stays
    ephemeral in slack-agent's in-memory cache, since losing an un-offered
    candidate on restart is low-harm (it just won't be re-detected until the
    next qualifying message/reaction).
    """

    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
