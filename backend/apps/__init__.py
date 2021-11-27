from motor.motor_asyncio import AsyncIOMotorClient


class DBConfigInterface:
    """
    Interface for configuring specific DB properties.
    """

    def setup(self, mongodb: AsyncIOMotorClient) -> None:
        """
        The method called at startup
        :parameter mongodb: The mongodb client.
        :return: None
        """
        pass
