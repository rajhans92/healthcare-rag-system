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
# from app.models.patient import Patient
from app.models.user import User
# from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)


class AuthService:

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

        if await self.user_repository.exists_by_email(
            request.email
        ):
            raise ValueError(
                "Email already registered."
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

        if request.role.value == "PATIENT":

            patient = Patient(
                user_id=user.id,
            )

            await self.patient_repository.create(
                patient
            )

        await self.session.commit()

        return RegisterResponse(
            message="Registration successful.",
            user=UserResponse.model_validate(user),
        )
    
    async def login(
        self,
        request: LoginRequest,
    ) -> LoginResponse:
        """
        Login user.
        """

        user = await self.user_repository.get_by_email(
            request.email
        )

        if user is None:
            raise ValueError(
                "Invalid credentials."
            )

        if not verify_password(
            request.password,
            user.password_hash,
        ):
            raise ValueError(
                "Invalid credentials."
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
