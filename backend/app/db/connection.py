"""
MongoDB connection management.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

# Global MongoDB client instance
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_to_mongo() -> None:
    """
    Creates a connection to MongoDB.
    Should be called on application startup.
    """
    global client, db
    try:
        client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
        )
        db = client[settings.MONGO_DB]
        # Verify connection
        await client.admin.command("ping")

        # Create indexes
        await create_indexes()

        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise


async def create_indexes():
    """Create database indexes for performance."""
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True, sparse=True)
    await db.movies.create_index([("title", 1), ("year", 1)])
    await db.movies.create_index("storage_id")
    await db.movies.create_index([("title", "text"), ("genre", "text")])


async def close_mongo_connection() -> None:
    """
    Closes MongoDB connection.
    Should be called on application shutdown.
    """
    if client is not None:
        client.close()
        print("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the database instance.
    To be used as a FastAPI dependency.
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db
