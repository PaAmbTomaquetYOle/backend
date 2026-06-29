from __future__ import annotations

from abc import ABC
from uuid import UUID, uuid4


class Id(ABC):
    """
    Abstract base class for IDs
    """
    __value: UUID
    
    def __init__(self, value: UUID | None = None) -> None:
        """
        Initializes the ID

        Args:
            value (UUID | None): the optional ID, if not passed, a random UUID is generated
        """
        if value is None:
            self.__value = uuid4()
        else:
            self.__value = value
        
    def get_id(self) -> UUID:
        """
        Returns the ID

        Returns:
            UUID: the new ID
        """
        return self.__value
    
    def set_id(self, id_value: UUID) -> None:
        """
        Sets the ID

        Args:
            id_value (UUID): the new ID
        """
        self.__value = id_value
        
    def regenerate_id(self) -> None:
        """
        Regenerates the ID
        """
        self.__value = uuid4()

    def is_equal(self, other: UUID | str | Id) -> bool:
        """
        Checks if two IDs are equal

        Args:
            other (UUID | str | Id): the other ID
        Returns:
            bool: whether the two IDs are equal
        """
        if isinstance(other, Id):
            return self.__value == other.get_id()
        elif isinstance(other, str):
            return self.__value == UUID(other)
        elif isinstance(other, UUID):
            return self.__value == other
        else:
            raise TypeError(f"Cannot compare Id with {type(other)}")


class OffboardingProcessId(Id):
    """
    Class representing an Offboarding Process ID
    """


class EmployeeId(Id):
    """
    Class representing an Employee ID
    """


class ManagerId(Id):
    """
    Class representing a Manager ID
    """


class InterviewId(Id):
    """Class representing an Interview ID"""


class DossierId(Id):
    """Class representing a Dossier ID"""
