"""
Centralised application configuration loaded from environment variables.
Uses pydantic-settings for validated, typed config with .env support.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings sourced from environment / .env file."""

    # MongoDB connection
    mongodb_url: str = "mongodb://127.0.0.1:27017"
    database_name: str = "child_profiles"

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton – import this instance everywhere
settings = Settings()
