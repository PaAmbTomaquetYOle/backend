"""Package representing IDs domain objects"""

from .id import DossierId, EmployeeId, Id, InterviewId, ManagerId, OffboardingProcessId
from .process import OffboardingProcess
from .state import (
    CancelledState,
    FinishedState,
    InProgressState,
    NotStartedState,
    OffboardingProcessState,
    PendingRevisionState,
)

__all__ = [
    'DossierId',
    'EmployeeId',
    'Id',
    'InterviewId',
    'ManagerId',
    'OffboardingProcessId',
    'OffboardingProcess',
    'CancelledState',
    'FinishedState',
    'InProgressState',
    'NotStartedState',
    'OffboardingProcessState',
    'PendingRevisionState',
]