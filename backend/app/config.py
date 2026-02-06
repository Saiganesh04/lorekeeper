"""Application configuration via pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Required
    anthropic_api_key: str

    # Database
    database_url: str = "sqlite+aiosqlite:///./lorekeeper.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # AI Model
    ai_model: str = "claude-sonnet-4-20250514"
    ai_max_tokens: int = 2000
    ai_temperature: float = 0.8

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # App info
    app_name: str = "Lorekeeper"
    app_version: str = "1.0.0"
    app_description: str = "AI-powered Dungeon Master for tabletop RPGs"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
