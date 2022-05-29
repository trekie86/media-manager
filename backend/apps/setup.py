from typing import Protocol
from motor.motor_asyncio import AsyncIOMotorClient

class Setup(Protocol):
    def setup(self, mongodb: AsyncIOMotorClient) -> None:
        """Setup the router"""