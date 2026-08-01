"""
JWT utility functions.

Responsible for:
- Creating access tokens
- Creating refresh tokens
- Decoding JWT tokens
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings


def _create_token(
    *,
    user_id: UUID,
    email: str,
    role: str,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """
    Create a JWT token.

    Args:
        user_id: User ID.
        email: User email.
        role: User role.
        expires_delta: Token expiration duration.
        token_type: access or refresh.

    Returns:
        Encoded JWT token.
    """

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    *,
    user_id: UUID,
    email: str,
    role: str,
) -> str:
    """
    Create an access token.
    """

    return _create_token(
        user_id=user_id,
        email=email,
        role=role,
        token_type="access",
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    )


def create_refresh_token(
    *,
    user_id: UUID,
    email: str,
    role: str,
) -> str:
    """
    Create a refresh token.
    """

    return _create_token(
        user_id=user_id,
        email=email,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT token.

    Args:
        token: JWT token.

    Returns:
        Decoded payload.

    Raises:
        JWTError: If the token is invalid or expired.
    """

    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )