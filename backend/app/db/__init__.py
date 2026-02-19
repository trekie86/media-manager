"""
Database package initialization.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from .connection import connect_to_mongo, close_mongo_connection, get_database
from .base import BaseRepository

__all__ = [
    "connect_to_mongo",
    "close_mongo_connection",
    "get_database",
    "BaseRepository",
    "get_repository",
]


def get_repository(
    database: AsyncIOMotorDatabase, collection_name: str
) -> BaseRepository:
    """
    Factory function to create repositories for specific collections.
    To be used as a FastAPI dependency.

    Args:
        database: MongoDB database instance
        collection_name: Name of the collection to create repository for

    Returns:
        BaseRepository instance for the specified collection
    """
    collection = database[collection_name]
    return BaseRepository(collection)
