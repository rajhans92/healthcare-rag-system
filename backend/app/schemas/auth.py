"""
Authentication request and response schemas.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

from app.models.user import UserRole, UserStatus
from app.schemas.patient import PatientResponse
from app.schemas.doctor import DoctorResponse

class RegisterRequest(BaseModel):
    """
    User registration request.
    """

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password",
    )

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    role: UserRole

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Validate password complexity.
        """

        if not any(c.isupper() for c in value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not any(c.islower() for c in value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not any(c.isdigit() for c in value):
            raise ValueError(
                "Password must contain at least one digit."
            )

        special_characters = "!@#$%^&*()_-+=[]{}|\\:;\"'<>,.?/"

        if not any(c in special_characters for c in value):
            raise ValueError(
                "Password must contain at least one special character."
            )

        return value


class LoginRequest(BaseModel):
    """
    User login request.
    """

    email: EmailStr

    password: str


class TokenResponse(BaseModel):
    """
    JWT token response.
    """

    access_token: str

    refresh_token: str

    token_type: str = "Bearer"


class UserResponse(BaseModel):
    """
    User information response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    email: EmailStr

    first_name: str

    last_name: str

    role: UserRole


class RegisterResponse(BaseModel):
    """
    Registration response.
    """

    message: str

    user: UserResponse


class LoginResponse(BaseModel):
    """
    Login response.
    """

    access_token: str

    refresh_token: str

    token_type: str = "Bearer"

    user: UserResponse

class CurrentUserResponse(BaseModel):

    id: UUID
    email: str
    first_name: str
    last_name: str

    role: UserRole
    status: UserStatus

    profile: PatientResponse | DoctorResponse | None