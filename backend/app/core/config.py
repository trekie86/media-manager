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
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    ENVIRONMENT: str = "development"
    
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
    SECRET_KEY: str = "change_me_in_production"  # Used for JWT signing
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # Get environment from the data being validated
        env = info.data.get("ENVIRONMENT", "development")
        
        if env == "production":
            # Ensure SECRET_KEY is not the default value in production
            if v == "change_me_in_production":
                raise ValueError("SECRET_KEY must be changed from default value")

            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    ALGORITHM: str = "HS256"  # JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    
    
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
    settings = Settings()
    
    if settings.ENVIRONMENT == "test":
        # Override settings for test environment
        settings.MONGO_HOST = "localhost"
        settings.MONGO_USER = "test_user"
        settings.MONGO_PASSWORD = "test_password"
        settings.MONGO_DB = "media_manager_test"
        settings.TMDB_API_KEY = "test_key"
    
    return settings


# Create global settings instance for non-test environments
settings = get_settings()
