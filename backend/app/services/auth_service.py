"""
Authentication service.

Contains all authentication business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.core.password import (
    hash_password,
    verify_password,
)
from app.enums.roles import Role
from app.exceptions.exceptions import (
    AuthenticationException,
    ConflictException,
)
from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from app.exceptions.error_codes import ErrorCode

class AuthService:
    """
    Authentication business service.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_repository = UserRepository(session)
        self.patient_repository = PatientRepository(session)

    async def register(
        self,
        request: RegisterRequest,
    ) -> RegisterResponse:
        """
        Register a new user.
        """

        try:

            # Check duplicate email
            if await self.user_repository.exists_by_email(
                request.email
            ):
                raise ConflictException(
                    message="Email already registered.",
                    code="EMAIL_ALREADY_EXISTS",
                )

            hashed_password = hash_password(
                request.password
            )

            user = User(
                email=request.email,
                password_hash=hashed_password,
                first_name=request.first_name,
                last_name=request.last_name,
                role=request.role,
            )

            user = await self.user_repository.create_user(
                user
            )

            # Automatically create Patient profile
            if request.role == Role.PATIENT:

                patient = Patient(
                    user_id=user.id,
                )

                await self.patient_repository.create(
                    patient
                )

            await self.session.commit()

            await self.session.refresh(user)

            return RegisterResponse(
                message="Registration successful.",
                user=UserResponse.model_validate(user),
            )

        except Exception:
            await self.session.rollback()
            raise

    async def login(
        self,
        request: LoginRequest,
    ) -> LoginResponse:
        """
        Authenticate user.
        """

        user = await self.user_repository.get_by_email(
            request.email
        )

        if user is None:
            raise AuthenticationException(
                message="Invalid email or password.",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        if not verify_password(
            request.password,
            user.password_hash,
        ):
            raise AuthenticationException(
                message="Invalid email or password.",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        await self.user_repository.update_last_login(
            user.id,
        )

        await self.session.commit()

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(
                user
            ),
        )