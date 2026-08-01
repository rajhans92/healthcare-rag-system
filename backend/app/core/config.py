"""
Application configuration.

Loads all application settings from environment variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    # ==========================
    # Application
    # ==========================

    APP_NAME: str = "Healthcare Knowledge RAG"

    APP_VERSION: str = "1.0.0"

    DEBUG: bool = False

    API_V1_PREFIX: str = "/api/v1"

    # ==========================
    # JWT
    # ==========================

    JWT_SECRET_KEY: str = Field(...)

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ==========================
    # AWS S3
    # ==========================

    AWS_REGION: str | None = None

    AWS_ACCESS_KEY_ID: str | None = None

    AWS_SECRET_ACCESS_KEY: str | None = None

    S3_BUCKET_NAME: str | None = None

    # ==========================
    # Qdrant
    # ==========================

    QDRANT_URL: str | None = None

    QDRANT_API_KEY: str | None = None

    # ==========================
    # OpenAI
    # ==========================

    OPENAI_API_KEY: str | None = None

    LLM_MODEL: str | None = None

    EMBEDDING_MODEL: str | None = None

    # ==========================
    # Database
    # ==========================

    DATABASE_URL: str

    DB_ECHO: bool = False

    DB_POOL_SIZE: int = 10

    DB_MAX_OVERFLOW: int = 20

    DB_POOL_TIMEOUT: int = 30

    DB_POOL_RECYCLE: int = 1800

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.
    """
    return Settings()

settings = Settings()