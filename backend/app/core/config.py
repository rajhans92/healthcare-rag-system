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
    AWS_S3_BUCKET_NAME: str | None = None

    # ==========================
    # Qdrant
    # ==========================

    VECTOR_DB_BACKEND: str = "memory"
    VECTOR_DB_HOST: str | None = None
    VECTOR_DB_PORT: int | None = None
    VECTOR_DB_NAME: str | None = None
    VECTOR_DB_USER: str | None = None
    VECTOR_DB_PASSWORD: str | None = None

    QDRANT_URL: str | None = None
    QDRANT_API_KEY: str | None = None

    # ==========================
    # OpenAI / LLM
    # ==========================

    OPENAI_API_KEY: str | None = None
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str | None = None
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DIMENSION: int = 32
    VECTOR_COLLECTION_NAME: str = "healthcare_documents"
    MAX_CONTEXT_TOKENS: int = 8000
    MAX_OUTPUT_TOKENS: int = 1000
    MAX_RETRIEVED_CHUNKS: int = 5

    # ==========================
    # OCR / Document parsing
    # ==========================

    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "eng"
    TESSERACT_CMD: str | None = None

    # ==========================
    # Database
    # ==========================

    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    AUTO_CREATE_TABLES: bool = False

    # ==========================
    # Background ingestion worker
    # ==========================

    INGESTION_WORKER_ENABLED: bool = True
    INGESTION_WORKER_INTERVAL_SECONDS: int = 30
    INGESTION_WORKER_BATCH_SIZE: int = 20

    # CORS settings for local development/debugging.
    # Set CORS_ALLOW_ALL=true to allow all origins (temporarily for local debugging).
    # Or set CORS_ALLOWED_ORIGINS="http://localhost:5173,https://example.com"
    CORS_ALLOW_ALL: bool = False
    CORS_ALLOWED_ORIGINS: str | None = None

@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.
    """
    return Settings()

settings = Settings()