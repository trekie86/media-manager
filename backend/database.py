from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


class database:
    def __init__(self) -> None:

        self.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
        self.mongodb = self.mongodb_client[settings.DB_NAME]


db = database()
