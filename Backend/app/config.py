"""Application configuration using pydantic-settings."""
import os
from functools import lru_cache


class Settings:
    """Application settings."""

    # API
    API_TITLE: str = "TrustBridge API"
    API_DESCRIPTION: str = "Alternative Trust Middleware for Unbanked Merchants"
    API_VERSION: str = "1.0.0"

    # Environment
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_random_secret_key_here")

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:trustbridge_password@localhost:5432/trustbridge"
    )

    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
