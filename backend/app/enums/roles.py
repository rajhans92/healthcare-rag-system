from enum import Enum


class Role(str, Enum):
    """
    System user roles.
    """

    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"