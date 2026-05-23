"""Configuration management using pydantic-settings."""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "CS Agent QA API"
    app_version: str = "1.0.0"
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # Server
    host: str
    port: int
    max_upload_bytes: int
    pipeline_concurrency: int

    # MongoDB
    mongodb_uri: str
    mongodb_db_name: str
    mongodb_collection_calls: str
    mongodb_timeout_ms: int

    # Gemini (Google AI)
    gemini_api_key: str
    gemini_model: str = "gemini-3.2-flash-lite"
    gemini_temperature: float = 0.2
    gemini_max_tokens: int = 4096

    # Langfuse (optional — observability)
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    class Config:
        """Pydantic settings config."""

        env_file = ".env"
        case_sensitive = False

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


settings = Settings()
