"""Enum of speaker roles in an interview turn."""

from enum import Enum


class SpeakerRoleEnum(Enum):
    """Enumeration of roles that can participate in an interview turn."""
    INTERVIEWER = "interviewer"
    INTERVIEWEE = "interviewee"
