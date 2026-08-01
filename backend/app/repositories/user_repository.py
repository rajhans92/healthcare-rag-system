"""
Repository for User entity.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User operations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Get user by email.
        """

        result = await self.session.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    async def exists_by_email(
        self,
        email: str,
    ) -> bool:

        result = await self.session.scalar(
            select(
                exists().where(User.email == email)
            )
        )

        return bool(result)

    async def update_last_login(
        self,
        user_id: UUID,
    ) -> None:
        """
        Update user's last login timestamp.
        """

        user = await self.get_by_id(user_id)

        if user is None:
            return

        user.last_login_at = datetime.now(timezone.utc)

        await self.session.flush()

    async def create_user(
        self,
        user: User,
    ) -> User:
        """
        Create new user.
        """

        return await self.create(user)