"""
Application configuration and settings.
"""
from typing import List

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
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
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


# Create global settings instance
settings = Settings()
