"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost/projectflow"
    )
    SECRET_KEY: str = Field(default="change-me-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    ALGORITHM: str = Field(default="HS256")
    PROJECT_NAME: str = Field(default="ProjectFlow")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
