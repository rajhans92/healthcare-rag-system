"""
Base repository.

Provides common CRUD operations for all repositories.
"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations.
    """

    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
    ):
        self.model = model
        self.session = session

    async def create(
        self,
        entity: ModelType,
    ) -> ModelType:
        """
        Create a new entity.
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)

        return entity

    async def get_by_id(
        self,
        entity_id: UUID,
    ) -> ModelType | None:
        """
        Retrieve an entity by its ID.
        """

        result = await self.session.execute(
            select(self.model).where(
                self.model.id == entity_id
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        """
        Retrieve all entities.
        """

        result = await self.session.execute(
            select(self.model)
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def update(
        self,
        entity: ModelType,
    ) -> ModelType:
        """
        Update an entity.
        """

        await self.session.flush()
        await self.session.refresh(entity)

        return entity

    async def delete(
        self,
        entity: ModelType,
    ) -> None:
        """
        Delete an entity.
        """

        await self.session.delete(entity)