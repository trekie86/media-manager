"""
Base repository pattern implementation for MongoDB collections.
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.results import DeleteResult, UpdateResult

T = TypeVar('T')  # Type for the document model


class BaseRepository(Generic[T]):
    """
    Base repository implementing common CRUD operations for MongoDB collections.
    """
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def find_one(self, query: Dict[str, Any]) -> Optional[T]:
        """
        Find a single document matching the query.
        """
        result = await self.collection.find_one(query)
        return result

    async def find_many(
        self,
        query: Dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """
        Find multiple documents matching the query.
        """
        cursor = self.collection.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return await cursor.to_list(length=None)

    async def insert_one(self, document: Dict[str, Any]) -> str:
        """
        Insert a single document and return its ID.
        """
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents and return their IDs.
        """
        result = await self.collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def update_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        *,
        upsert: bool = False
    ) -> UpdateResult:
        """
        Update a single document matching the query.
        """
        return await self.collection.update_one(
            query,
            {'$set': update},
            upsert=upsert
        )

    async def update_many(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> UpdateResult:
        """
        Update multiple documents matching the query.
        """
        return await self.collection.update_many(
            query,
            {'$set': update}
        )

    async def delete_one(self, query: Dict[str, Any]) -> DeleteResult:
        """
        Delete a single document matching the query.
        """
        return await self.collection.delete_one(query)

    async def delete_many(self, query: Dict[str, Any]) -> DeleteResult:
        """
        Delete multiple documents matching the query.
        """
        return await self.collection.delete_many(query)

    async def count(self, query: Dict[str, Any]) -> int:
        """
        Count documents matching the query.
        """
        return await self.collection.count_documents(query)

    def get_by_id(self, id: str) -> Optional[T]:
        """
        Find a document by its ID.
        """
        return self.find_one({'_id': ObjectId(id)})
