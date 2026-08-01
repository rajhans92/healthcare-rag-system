from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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


settings = Settings()