"""
Authentication and application dependencies.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import decode_token
from app.db.database import get_db
from app.exceptions.error_codes import ErrorCode
from app.exceptions.exceptions import (
    AuthenticationException,
    AuthorizationException,
)
from app.models.user import (
    User,
    UserStatus,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.doctor_service import DoctorService
from app.services.patient_service import PatientService

# -------------------------------------------------------------------------
# Security
# -------------------------------------------------------------------------

security = HTTPBearer(
    auto_error=False,
)


# -------------------------------------------------------------------------
# Current User Dependency
# -------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Returns the currently authenticated user.
    """

    if credentials is None:
        raise AuthenticationException(
            message="Authentication token is missing.",
            code=ErrorCode.UNAUTHORIZED,
        )

    try:

        payload = decode_token(
            credentials.credentials,
        )

        user_id = payload.get("sub")

        if not user_id:
            raise AuthenticationException(
                message="Invalid authentication token.",
                code=ErrorCode.INVALID_TOKEN,
            )

        user_uuid = UUID(user_id)

    except (JWTError, ValueError, TypeError):

        raise AuthenticationException(
            message="Invalid authentication token.",
            code=ErrorCode.INVALID_TOKEN,
        )

    repository = UserRepository(db)

    user = await repository.get_by_id(
        user_uuid,
    )

    if user is None:
        raise AuthenticationException(
            message="User not found.",
            code=ErrorCode.INVALID_TOKEN,
        )

    if user.status != UserStatus.ACTIVE:
        raise AuthorizationException(
            message="User account is inactive.",
        )

    return user


# -------------------------------------------------------------------------
# Service Dependencies
# -------------------------------------------------------------------------

def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """
    Returns AuthService instance.
    """

    return AuthService(db)


def get_patient_service(
    db: AsyncSession = Depends(get_db),
) -> PatientService:
    """
    Returns PatientService instance.
    """

    return PatientService(db)


def get_doctor_service(
    db: AsyncSession = Depends(get_db),
) -> DoctorService:
    """
    Returns DoctorService instance.
    """

    return DoctorService(db)

async def require_doctor(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require the authenticated user to be a doctor.
    """

    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required.",
        )

    return current_user

# -------------------------------------------------------------------------
# User Dependencies
# -------------------------------------------------------------------------

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]