"""
Application configuration and settings.
"""
import os
from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings and environment variables.
    """
    # API Configuration
    PROJECT_NAME: str = "Media Manager API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parse CORS_ORIGINS from string or list.
        Example: "http://localhost:3000,http://localhost:8000" -> ["http://localhost:3000", "http://localhost:8000"]
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # MongoDB Configuration
    MONGO_HOST: str = "mongodb"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "media_manager"
    MONGO_USER: str
    MONGO_PASSWORD: str
    
    # TMDB Configuration
    TMDB_API_KEY: str
    TMDB_API_URL: str = "https://api.themoviedb.org/3"
    
    # Authentication
    SECRET_KEY: str = "change_me_in_production"  # Used for session encryption
    SESSION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def mongodb_url(self) -> str:
        """
        Constructs MongoDB connection URL from settings.
        """
        return (
            f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"
        )


# Settings instance factory
@lru_cache
def get_settings() -> Settings:
    """
    Create cached settings instance based on environment.
    For testing, override settings with test-specific values.
    """
    env = os.getenv("ENVIRONMENT", "development")
    settings = Settings()
    
    if env == "test":
        # Override settings for test environment
        settings.MONGO_HOST = "localhost"
        settings.MONGO_USER = "test"
        settings.MONGO_PASSWORD = "test"
        settings.MONGO_DB = "media_manager_test"
        settings.TMDB_API_KEY = "test_key"
    
    return settings


# Create global settings instance for non-test environments
settings = get_settings()
