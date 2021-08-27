import sec
from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    APP_NAME: str = "Media Manager"
    DEBUG_MODE: bool = False


class DatabaseSettings(BaseSettings):
    DB_URL: str = sec.load("MONGODB_CONNECTION_STRING")
    DB_NAME: str = sec.load("MONGODB_NAME")


class Settings(CommonSettings, DatabaseSettings):
    pass


settings = Settings()
