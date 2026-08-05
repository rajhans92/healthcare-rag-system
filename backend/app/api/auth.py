"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import (
    CurrentUser,
    get_auth_service,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.schemas.auth import CurrentUserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Register a new user.
    """

    return await service.register(request)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Authenticate user.
    """

    return await service.login(request)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
async def me(
    current_user: CurrentUser,
    service: AuthService = Depends(get_auth_service),
):

    return await service.get_current_user_profile(
        current_user,
    )