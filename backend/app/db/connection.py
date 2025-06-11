"""
MongoDB connection management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

from app.core.config import settings

# Global MongoDB client instance
client: AsyncIOMotorClient = None
db: Database = None


async def connect_to_mongo() -> None:
    """
    Creates a connection to MongoDB.
    Should be called on application startup.
    """
    global client, db
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.MONGO_DB]
        # Verify connection
        await client.admin.command('ping')
        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Closes MongoDB connection.
    Should be called on application shutdown.
    """
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


def get_database() -> Database:
    """
    Returns the database instance.
    To be used as a FastAPI dependency.
    """
    if not db:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db
