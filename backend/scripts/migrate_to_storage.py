"""
Migration script to convert from bin-based to hierarchical storage model.
"""
import asyncio
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING

# MongoDB connection settings
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "media_manager"

async def migrate_to_storage():
    """
    Migrate the database from bin-based to hierarchical storage model.
    
    Steps:
    1. Rename bins collection to storage
    2. Convert existing bins to storage nodes
    3. Update movie references
    4. Add indexes for tree operations
    """
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        # 1. Rename bins collection to storage
        try:
            await db.bins.rename("storage")
            print("✓ Renamed bins collection to storage")
        except Exception as e:
            if "source namespace does not exist" in str(e):
                print("✓ Storage collection already exists")
            else:
                raise

        # 2. Convert existing bins to storage nodes
        async for doc in db.storage.find({}):
            # Skip if already migrated
            if "type" in doc:
                continue
                
            # Convert bin to storage node
            update = {
                "$set": {
                    "type": "bin",  # Default type for existing bins
                    "path": [],     # Empty path as these are root nodes
                    "metadata": {   # Initialize metadata structure
                        "capacity": None,
                        "dimensions": None,
                        "location": None,
                        "custom": {}
                    }
                }
            }
            
            result = await db.storage.update_one(
                {"_id": doc["_id"]},
                update
            )
            print(f"✓ Converted storage node: {doc.get('name', str(doc['_id']))}")

        # 3. Update movie references
        # Find movies with bin_id and update to storage_id
        async for movie in db.movies.find({"bin_id": {"$exists": True}}):
            result = await db.movies.update_one(
                {"_id": movie["_id"]},
                {
                    "$rename": {"bin_id": "storage_id"}
                }
            )
            print(f"✓ Updated movie reference: {movie.get('title', str(movie['_id']))}")

        # 4. Add indexes for tree operations
        indexes: List[IndexModel] = [
            IndexModel([("parent_id", ASCENDING)], 
                      name="parent_id_idx"),
            IndexModel([("path", ASCENDING)], 
                      name="path_idx"),
            IndexModel([("type", ASCENDING)], 
                      name="type_idx"),
            # Compound indexes for common queries
            IndexModel([("parent_id", ASCENDING), ("type", ASCENDING)],
                      name="parent_type_idx"),
            IndexModel([("path", ASCENDING), ("type", ASCENDING)],
                      name="path_type_idx")
        ]
        
        await db.storage.create_indexes(indexes)
        print("✓ Created indexes for tree operations")
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_to_storage())
