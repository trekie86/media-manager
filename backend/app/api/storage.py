"""Storage routes for managing storage locations."""
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.errors import DuplicateKeyError

from app.db.connection import get_database
from app.models.storage import (
    StorageCreate, StorageResponse, StorageUpdate, StorageTreeResponse
)

# Setup router
router = APIRouter()

@router.post("", response_model=StorageResponse, status_code=status.HTTP_201_CREATED)
async def create_storage(storage_data_input: dict, db=Depends(get_database)):
    """Create a new storage location."""
    # Check if name already exists
    if await db.storage.find_one({"name": storage_data_input["name"]}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage name already exists"
        )
    
    # Initialize path as empty list if not set
    if "path" not in storage_data_input:
        storage_data_input["path"] = []
    
    # If parent_id is provided, validate it exists and update path
    if "parent_id" in storage_data_input and storage_data_input["parent_id"]:
        try:
            parent_oid = ObjectId(storage_data_input["parent_id"])
            parent = await db.storage.find_one({"_id": parent_oid})
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent storage location not found"
                )
            
            # Set path based on parent's path
            parent_path = parent.get("path", [])
            # Convert path to ObjectId for MongoDB
            storage_data_input["path"] = parent_path + [parent_oid]
        except Exception as e:
            if "Invalid ObjectId" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid parent ID format"
                )
            raise
    
    # Create storage document
    try:
        # Convert to dict for MongoDB
        storage_dict = dict(storage_data_input)
        
        # Convert parent_id to ObjectId if present
        if "parent_id" in storage_dict and storage_dict["parent_id"]:
            storage_dict["parent_id"] = ObjectId(storage_dict["parent_id"])
        
        result = await db.storage.insert_one(storage_dict)
        storage_id = str(result.inserted_id)
        
        # Retrieve the created storage for response
        created_storage = await db.storage.find_one({"_id": result.inserted_id})
        
        # Convert ObjectId to string for response
        response_data = {
            "id": storage_id,
            "name": created_storage["name"],
            "description": created_storage.get("description"),
            "type": created_storage["type"],
            "parent_id": str(created_storage["parent_id"]) if created_storage.get("parent_id") else None,
            "path": [str(p) for p in created_storage.get("path", [])],
            "metadata": created_storage.get("metadata", {})
        }
        
        return StorageResponse(**response_data)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage name already exists"
        )

@router.get("", response_model=List[StorageResponse])
async def list_storage(
    parent_id: Optional[str] = None,
    type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database)
):
    """List storage locations with optional filtering."""
    # Build query
    query = {}
    if parent_id:
        try:
            query["parent_id"] = ObjectId(parent_id)
        except Exception:
            # If invalid ObjectId, return empty list (no results will match)
            return []
    if type:
        query["type"] = type
    
    # Execute query
    cursor = db.storage.find(query).skip(skip).limit(limit)
    storage_list = await cursor.to_list(length=limit)
    
    # Convert to response models
    result = []
    for item in storage_list:
        # Convert ObjectId to string
        item_dict = {
            "id": str(item["_id"]),
            "name": item["name"],
            "description": item.get("description"),
            "type": item["type"],
            "parent_id": str(item["parent_id"]) if item.get("parent_id") else None,
            "path": [str(p) for p in item.get("path", [])],
            "metadata": item.get("metadata", {})
        }
        result.append(StorageResponse(**item_dict))
    
    return result

@router.get("/{storage_id}", response_model=StorageResponse)
async def get_storage(storage_id: str, db=Depends(get_database)):
    """Get a specific storage location by ID."""
    try:
        storage = await db.storage.find_one({"_id": ObjectId(storage_id)})
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage location not found"
            )
        
        # Get movies in this storage location
        movies_cursor = db.movies.find({"storage_id": ObjectId(storage_id)})
        movies = await movies_cursor.to_list(length=100)
        
        # Convert movie ObjectIds to strings
        movies_list = []
        for movie in movies:
            movie_dict = {
                "id": str(movie["_id"]),
                "title": movie["title"],
                "year": movie["year"],
                "format": movie["format"],
                "storage_id": str(movie["storage_id"]),
                "tmdb_id": movie.get("tmdb_id"),
                "genre": movie.get("genre", []),
                "runtime": movie.get("runtime"),
                "cover_image": movie.get("cover_image")
            }
            movies_list.append(movie_dict)
        
        # Get children storage locations
        children_cursor = db.storage.find({"parent_id": ObjectId(storage_id)})
        children = await children_cursor.to_list(length=100)
        
        # Convert children ObjectIds to strings
        children_list = []
        for child in children:
            child_dict = {
                "id": str(child["_id"]),
                "name": child["name"],
                "description": child.get("description"),
                "type": child["type"],
                "parent_id": str(child["parent_id"]) if child.get("parent_id") else None,
                "path": [str(p) for p in child.get("path", [])],
                "metadata": child.get("metadata", {})
            }
            children_list.append(StorageResponse(**child_dict))
        
        # Build response
        response_data = {
            "id": str(storage["_id"]),
            "name": storage["name"],
            "description": storage.get("description"),
            "type": storage["type"],
            "parent_id": str(storage["parent_id"]) if storage.get("parent_id") else None,
            "path": [str(p) for p in storage.get("path", [])],
            "metadata": storage.get("metadata", {}),
            "movies": movies_list,
            "children": children_list
        }
        
        return StorageResponse(**response_data)
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid storage ID format"
            )
        raise

@router.get("/{storage_id}/tree", response_model=StorageTreeResponse)
async def get_storage_tree(storage_id: str, db=Depends(get_database)):
    """Get a storage location with its full tree (ancestors and descendants)."""
    try:
        storage_oid = ObjectId(storage_id)
        
        # Get the storage location
        storage = await db.storage.find_one({"_id": storage_oid})
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage location not found"
            )
        
        # Get ancestors
        ancestors = []
        if storage.get("path"):
            ancestor_ids = [ObjectId(p) if isinstance(p, str) else p for p in storage.get("path", [])]
            ancestors_cursor = db.storage.find({"_id": {"$in": ancestor_ids}})
            ancestors = await ancestors_cursor.to_list(length=100)
            
            # Convert ancestor ObjectIds to strings for response
            ancestors_list = []
            for ancestor in ancestors:
                ancestor_dict = {
                    "id": str(ancestor["_id"]),
                    "name": ancestor["name"],
                    "description": ancestor.get("description"),
                    "type": ancestor["type"],
                    "parent_id": str(ancestor["parent_id"]) if ancestor.get("parent_id") else None,
                    "path": [str(p) for p in ancestor.get("path", [])],
                    "metadata": ancestor.get("metadata", {})
                }
                ancestors_list.append(ancestor_dict)
        
        # Get descendants (all storage items that have this ID in their path)
        descendants_cursor = db.storage.find({"path": storage_oid})
        descendants = await descendants_cursor.to_list(length=1000)
        
        # Convert descendant ObjectIds to strings for response
        descendants_list = []
        for descendant in descendants:
            descendant_dict = {
                "id": str(descendant["_id"]),
                "name": descendant["name"],
                "description": descendant.get("description"),
                "type": descendant["type"],
                "parent_id": str(descendant["parent_id"]) if descendant.get("parent_id") else None,
                "path": [str(p) for p in descendant.get("path", [])],
                "metadata": descendant.get("metadata", {})
            }
            descendants_list.append(descendant_dict)
        
        # Get movies in this storage location
        movies_cursor = db.movies.find({"storage_id": storage_oid})
        movies = await movies_cursor.to_list(length=100)
        
        # Convert movie ObjectIds to strings for response
        movies_list = []
        for movie in movies:
            movie_dict = {
                "id": str(movie["_id"]),
                "title": movie["title"],
                "year": movie["year"],
                "format": movie["format"],
                "storage_id": str(movie["storage_id"]),
                "tmdb_id": movie.get("tmdb_id"),
                "genre": movie.get("genre", []),
                "runtime": movie.get("runtime"),
                "cover_image": movie.get("cover_image")
            }
            movies_list.append(movie_dict)
        
        # Get immediate children
        children_cursor = db.storage.find({"parent_id": storage_oid})
        children = await children_cursor.to_list(length=100)
        
        # Convert children ObjectIds to strings for response
        children_list = []
        for child in children:
            child_dict = {
                "id": str(child["_id"]),
                "name": child["name"],
                "description": child.get("description"),
                "type": child["type"],
                "parent_id": str(child["parent_id"]) if child.get("parent_id") else None,
                "path": [str(p) for p in child.get("path", [])],
                "metadata": child.get("metadata", {})
            }
            children_list.append(child_dict)
        
        # Build response
        response_data = {
            "id": str(storage["_id"]),
            "name": storage["name"],
            "description": storage.get("description"),
            "type": storage["type"],
            "parent_id": str(storage["parent_id"]) if storage.get("parent_id") else None,
            "path": [str(p) for p in storage.get("path", [])],
            "metadata": storage.get("metadata", {}),
            "movies": movies_list,
            "children": [StorageResponse(**child) for child in children_list],
            "ancestors": [StorageResponse(**ancestor) for ancestor in ancestors_list],
            "descendants": [StorageResponse(**descendant) for descendant in descendants_list]
        }
        
        return StorageTreeResponse(**response_data)
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid storage ID format"
            )
        raise

@router.put("/{storage_id}", response_model=StorageResponse)
async def update_storage(
    storage_id: str,
    storage_data: StorageUpdate,
    db=Depends(get_database)
):
    """Update a storage location."""
    try:
        storage_oid = ObjectId(storage_id)
        
        # Check if storage exists
        storage = await db.storage.find_one({"_id": storage_oid})
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage location not found"
            )
        
        # Prepare update data
        update_data = storage_data.model_dump(exclude_unset=True)
        
        # If parent_id is being updated, validate and update path
        if "parent_id" in update_data:
            # Prevent circular references
            if update_data["parent_id"] == storage_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Storage location cannot be its own parent"
                )
            
            # Convert parent_id to ObjectId
            parent_oid = ObjectId(update_data["parent_id"])
            update_data["parent_id"] = parent_oid
            
            # Check if new parent exists
            parent = await db.storage.find_one({"_id": parent_oid})
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent storage location not found"
                )
            
            # Check if new parent is not a descendant of this storage
            if storage_oid in parent.get("path", []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot set a descendant as parent (would create a cycle)"
                )
            
            # Update path
            update_data["path"] = parent.get("path", []) + [parent_oid]
            
            # Update paths of all descendants
            old_path_prefix = storage.get("path", []) + [storage_oid]
            new_path_prefix = update_data["path"] + [storage_oid]
            
            # Find all descendants
            descendants = await db.storage.find({"path": storage_oid}).to_list(length=1000)
            
            # Update each descendant's path
            for descendant in descendants:
                # Find where in the path the current storage appears
                idx = [str(p) for p in descendant["path"]].index(str(storage_oid))
                # Replace the path up to and including the current storage with the new path
                descendant_new_path = new_path_prefix + descendant["path"][idx+1:]
                await db.storage.update_one(
                    {"_id": descendant["_id"]},
                    {"$set": {"path": descendant_new_path}}
                )
        
        # Update the storage document
        try:
            await db.storage.update_one(
                {"_id": storage_oid},
                {"$set": update_data}
            )
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Storage name already exists"
            )
        
        # Get updated storage
        updated_storage = await db.storage.find_one({"_id": storage_oid})
        
        # Create response data with proper ID field
        response_data = {
            "id": str(updated_storage["_id"]),
            "name": updated_storage["name"],
            "description": updated_storage.get("description"),
            "type": updated_storage["type"],
            "parent_id": str(updated_storage["parent_id"]) if updated_storage.get("parent_id") else None,
            "path": [str(p) for p in updated_storage.get("path", [])],
            "metadata": updated_storage.get("metadata", {})
        }
        
        return StorageResponse(**response_data)
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid storage ID format"
            )
        raise

@router.delete("/{storage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage(storage_id: str, db=Depends(get_database)):
    """Delete a storage location."""
    try:
        storage_oid = ObjectId(storage_id)
        
        # Check if storage exists
        storage = await db.storage.find_one({"_id": storage_oid})
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage location not found"
            )
        
        # Check if storage has children
        children_count = await db.storage.count_documents({"parent_id": storage_oid})
        if children_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete storage with children. Delete children first."
            )
        
        # Check if storage has movies
        movies_count = await db.movies.count_documents({"storage_id": storage_oid})
        if movies_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete storage with movies. Move or delete movies first."
            )
        
        # Delete storage
        await db.storage.delete_one({"_id": storage_oid})
        
        return None
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid storage ID format"
            )
        raise
