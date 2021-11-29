import sec
from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    APP_NAME: str = "Media Manager"
    DEBUG_MODE: bool = True


class DatabaseSettings(BaseSettings):
    MONGODB_USER: str = sec.load("mongodb_user")
    MONGODB_PASSWORD: str = sec.load("mongodb_password")
    DB_URL: str = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@mongo:27017/"
    DB_NAME: str = 'media-manager'


class MovieDBSettings(BaseSettings):
    TMDB_V3_TOKEN: str = sec.load("tmdb_v3_token")
    TMDB_V4_TOKEN: str = sec.load("tmdb_v4_token")


class Settings(CommonSettings, DatabaseSettings, MovieDBSettings):
    pass


settings = Settings()
