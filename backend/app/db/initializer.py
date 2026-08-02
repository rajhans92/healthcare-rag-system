from app.core.config import settings
from app.db.base import Base
from app.db.database import engine


async def initialize_database() -> None:
    """
    Initialize database schema for development.
    """

    if not settings.AUTO_CREATE_TABLES:
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)