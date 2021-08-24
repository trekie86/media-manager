import sec
from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    APP_NAME: str = "Media Manager"
    DEBUG_MODE: bool = False


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8080


class DatabaseSettings(BaseSettings):
    DB_URL: str = sec.load("MONGODB_CONNECTION_STRING")
    DB_NAME: str = sec.load("MONGODB_NAME")


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()
