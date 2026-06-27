from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.offboarding import EmployeeId, ManagerId, OffboardingProcessId
    from app.domain.offboarding.state import OffboardingProcessState


class OffboardingProcess:
    __id: OffboardingProcessId
    __state: OffboardingProcessState
    __employee_id: EmployeeId
    __manager_id: ManagerId
    __created_at: datetime

    def __init__(
            self,
            process_id: OffboardingProcessId,
            state: OffboardingProcessState,
            employee_id: EmployeeId,
            manager_id: ManagerId,
            created_at: datetime
    ):
        self.__id = process_id
        self.__state = state
        self.__employee_id = employee_id
        self.__manager_id = manager_id
        self.__created_at = created_at

    @property
    def process_id(self) -> OffboardingProcessId:
        return self.__id

    @process_id.setter
    def process_id(self, process_id: OffboardingProcessId):
        self.__id = process_id

    @property
    def state(self) -> OffboardingProcessState:
        return self.__state

    @state.setter
    def state(self, state: OffboardingProcessState):
        self.__state = state

    @property
    def employee_id(self) -> EmployeeId:
        return self.__employee_id

    @employee_id.setter
    def employee_id(self, employee_id: EmployeeId):
        self.__employee_id = employee_id

    @property
    def manager_id(self) -> ManagerId:
        return self.__manager_id

    @manager_id.setter
    def manager_id(self, manager_id: ManagerId):
        self.__manager_id = manager_id

    @property
    def created_at(self) -> datetime:
        return self.__created_at

    @created_at.setter
    def created_at(self, created_at: datetime):
        self.__created_at = created_at