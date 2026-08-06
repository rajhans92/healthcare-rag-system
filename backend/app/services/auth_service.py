"""
Authentication service.

Contains all authentication business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
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
from app.schemas.auth import CurrentUserResponse
from app.repositories.doctor_repository import DoctorRepository
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

from app.schemas.doctor import DoctorResponse
from app.schemas.patient import PatientResponse
from app.exceptions.exceptions import ResourceNotFoundException

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
        self.doctor_repository = DoctorRepository(session)

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
                    code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

            hashed_password = hash_password(
                request.password
            )

            user = User(
                email=request.email,
                password_hash=hashed_password,
                first_name=request.first_name,
                last_name=request.last_name,
                role=request.role.value,
            )

            user = await self.user_repository.create_user(
                user
            )

            if request.role == Role.PATIENT:
                await self.patient_repository.create_for_user(
                    user.id
                )

            elif request.role == Role.DOCTOR:
                await self.doctor_repository.create_for_user(
                    user.id
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
        
    async def get_current_user_profile(
        self,
        current_user: User,
    ) -> CurrentUserResponse:

        profile = None

        if current_user.role.value == Role.PATIENT.value:

            patient = await self.patient_repository.get_by_user_id(
                current_user.id,
            )

            if patient:
                profile = PatientResponse.model_validate(
                    patient
                )

        elif current_user.role.value == Role.DOCTOR.value:

            doctor = await self.doctor_repository.get_by_user_id(
                current_user.id,
            )

            if doctor:
                profile = DoctorResponse.model_validate(
                    doctor
                )

        return CurrentUserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            role=current_user.role.value,
            status=current_user.status,
            profile=profile,
        )
    
    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> UserResponse:

        user = await self.user_repository.get_by_id(
            user_id
        )

        if user is None:
            raise ResourceNotFoundException("User")

        return UserResponse.model_validate(user)