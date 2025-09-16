"""
Movie API endpoints for CRUD operations.
"""
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.errors import DuplicateKeyError

from ..db.connection import get_database
from ..models.movie import MovieCreate, MovieResponse, MovieUpdate

router = APIRouter()


@router.post("/", response_model=MovieResponse, status_code=201)
async def create_movie(movie: MovieCreate, db=Depends(get_database)) -> MovieResponse:
    """
    Create a new movie.
    """
    
    # Validate that storage_id exists
    try:
        storage_id = ObjectId(movie.storage_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid storage_id format")
    
    storage = await db.storage.find_one({"_id": storage_id})
    if not storage:
        raise HTTPException(status_code=404, detail="Storage location not found")
    
    # Convert movie data for MongoDB, excluding None values
    movie_data = movie.model_dump(exclude_none=True)
    movie_data["storage_id"] = storage_id
    
    try:
        result = await db.movies.insert_one(movie_data)
        
        # Fetch the created movie
        created_movie = await db.movies.find_one({"_id": result.inserted_id})
        if not created_movie:
            raise HTTPException(status_code=500, detail="Failed to retrieve created movie")
        
        # Convert ObjectId to string for response
        response_data = {
            "id": str(created_movie["_id"]),
            "title": created_movie["title"],
            "year": created_movie["year"],
            "format": created_movie["format"],
            "storage_id": str(created_movie["storage_id"]),
            "tmdb_id": created_movie.get("tmdb_id"),
            "genre": created_movie.get("genre"),
            "runtime": created_movie.get("runtime"),
            "cover_image": created_movie.get("cover_image")
        }
        
        return MovieResponse(**response_data)
        
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Movie already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create movie: {str(e)}")


@router.get("/", response_model=List[MovieResponse])
async def list_movies(
    skip: int = Query(0, ge=0, description="Number of movies to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of movies to return"),
    storage_id: Optional[str] = Query(None, description="Filter by storage location"),
    format: Optional[str] = Query(None, description="Filter by media format"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    db=Depends(get_database)
) -> List[MovieResponse]:
    """
    List movies with optional filtering.
    """
    
    # Build filter query
    filter_query = {}
    
    if storage_id:
        try:
            filter_query["storage_id"] = ObjectId(storage_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid storage_id format")
    
    if format:
        filter_query["format"] = format
    
    if genre:
        filter_query["genre"] = {"$in": [genre]}
    
    try:
        cursor = db.movies.find(filter_query).skip(skip).limit(limit)
        movies = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings for response
        response_movies = []
        for movie in movies:
            response_data = {
                "id": str(movie["_id"]),
                "title": movie["title"],
                "year": movie["year"],
                "format": movie["format"],
                "storage_id": str(movie["storage_id"]),
                "tmdb_id": movie.get("tmdb_id"),
                "genre": movie.get("genre"),
                "runtime": movie.get("runtime"),
                "cover_image": movie.get("cover_image")
            }
            response_movies.append(MovieResponse(**response_data))
        
        return response_movies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list movies: {str(e)}")


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: str, db=Depends(get_database)) -> MovieResponse:
    """
    Get a specific movie by ID.
    """
    
    try:
        object_id = ObjectId(movie_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")
    
    try:
        movie = await db.movies.find_one({"_id": object_id})
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Convert ObjectId to string for response
        response_data = {
            "id": str(movie["_id"]),
            "title": movie["title"],
            "year": movie["year"],
            "format": movie["format"],
            "storage_id": str(movie["storage_id"]),
            "tmdb_id": movie.get("tmdb_id"),
            "genre": movie.get("genre"),
            "runtime": movie.get("runtime"),
            "cover_image": movie.get("cover_image")
        }
        
        return MovieResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get movie: {str(e)}")


@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(movie_id: str, movie_update: MovieUpdate, db=Depends(get_database)) -> MovieResponse:
    """
    Update an existing movie.
    """
    
    try:
        object_id = ObjectId(movie_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")
    
    # Check if movie exists
    existing_movie = await db.movies.find_one({"_id": object_id})
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Build update data, excluding None values
    update_data = {}
    for field, value in movie_update.model_dump(exclude_unset=True).items():
        if value is not None:
            if field == "storage_id":
                # Validate storage_id exists
                try:
                    storage_id = ObjectId(value)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid storage_id format")
                
                storage = await db.storage.find_one({"_id": storage_id})
                if not storage:
                    raise HTTPException(status_code=404, detail="Storage location not found")
                update_data[field] = storage_id
            else:
                update_data[field] = value
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    try:
        result = await db.movies.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Fetch updated movie
        updated_movie = await db.movies.find_one({"_id": object_id})
        if not updated_movie:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated movie")
        
        # Convert ObjectId to string for response
        response_data = {
            "id": str(updated_movie["_id"]),
            "title": updated_movie["title"],
            "year": updated_movie["year"],
            "format": updated_movie["format"],
            "storage_id": str(updated_movie["storage_id"]),
            "tmdb_id": updated_movie.get("tmdb_id"),
            "genre": updated_movie.get("genre"),
            "runtime": updated_movie.get("runtime"),
            "cover_image": updated_movie.get("cover_image")
        }
        
        return MovieResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update movie: {str(e)}")


@router.delete("/{movie_id}", status_code=204)
async def delete_movie(movie_id: str, db=Depends(get_database)) -> None:
    """
    Delete a movie.
    """
    
    try:
        object_id = ObjectId(movie_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")
    
    try:
        result = await db.movies.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Movie not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete movie: {str(e)}")
