"""
Movie API endpoints for CRUD operations.
"""

from typing import List, Optional, Dict, Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pymongo.errors import DuplicateKeyError

from ..db.connection import get_database
from ..models.movie import MovieCreate, MovieResponse, MovieUpdate
from ..services.tmdb import get_tmdb_service, TMDBService
from ..services.genre import upsert_genres

router = APIRouter()

# Upper bound for descendant lookups — prevents unbounded to_list() calls.
_MAX_STORAGE_DESCENDANTS = 10_000


async def _build_storage_filter(
    db, storage_oid: ObjectId, include_descendants: bool
) -> Dict[str, Any]:
    """Return a MongoDB filter dict for storage_id, optionally spanning descendants.

    When include_descendants is True the materialized-path index is used to
    find all descendant nodes and the filter uses $in across the full subtree.
    """
    if include_descendants:
        cursor = db.storage.find({"path": storage_oid}, {"_id": 1})
        descendants = await cursor.to_list(length=_MAX_STORAGE_DESCENDANTS)
        descendant_ids = [d["_id"] for d in descendants]
        return {"storage_id": {"$in": [storage_oid] + descendant_ids}}
    return {"storage_id": storage_oid}


def _movie_to_response(movie: dict) -> MovieResponse:
    """Convert a raw MongoDB movie document to a MovieResponse."""
    return MovieResponse(
        id=str(movie["_id"]),
        title=movie["title"],
        year=movie["year"],
        format=movie["format"],
        storage_id=str(movie["storage_id"]),
        tmdb_id=movie.get("tmdb_id"),
        genre_ids=movie.get("genre_ids"),
        runtime=movie.get("runtime"),
        cover_image=movie.get("cover_image"),
    )


@router.post("/", response_model=MovieResponse, status_code=201)
async def create_movie(
    movie: MovieCreate,
    db=Depends(get_database),
    tmdb: TMDBService = Depends(get_tmdb_service),
) -> MovieResponse:
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

    # Auto-enrich from TMDB if tmdb_id provided and any enrichable field is missing
    needs_enrichment = not movie.genre_ids or not movie.runtime or not movie.cover_image
    if movie.tmdb_id and needs_enrichment:
        try:
            details = await tmdb.get_movie_details(movie.tmdb_id)
            if details:
                if not movie.genre_ids and details.get("genre_ids"):
                    movie_data["genre_ids"] = details["genre_ids"]
                    # Persist any newly discovered genres to the genres collection
                    await upsert_genres(db, details.get("genres", []))
                if not movie.runtime and details.get("runtime"):
                    movie_data["runtime"] = details["runtime"]
                if not movie.cover_image and details.get("poster_url"):
                    movie_data["cover_image"] = details["poster_url"]
        except Exception:
            logger.warning(
                f"TMDB auto-enrichment failed for tmdb_id={movie.tmdb_id},"
                " proceeding without enrichment"
            )
    try:
        result = await db.movies.insert_one(movie_data)

        # Fetch the created movie
        created_movie = await db.movies.find_one({"_id": result.inserted_id})
        if not created_movie:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve created movie"
            )

        return _movie_to_response(created_movie)

    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Movie already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create movie: {str(e)}")


@router.get("/", response_model=List[MovieResponse])
async def list_movies(
    skip: int = Query(0, ge=0, description="Number of movies to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of movies to return"),
    storage_id: Optional[str] = Query(None, description="Filter by storage location"),
    include_descendants: bool = Query(
        False, description="Include movies from descendant storage locations"
    ),
    format: Optional[str] = Query(None, description="Filter by media format"),
    genre_id: Optional[int] = Query(None, description="Filter by TMDB genre ID"),
    db=Depends(get_database),
) -> List[MovieResponse]:
    """
    List movies with optional filtering.
    """

    # Build filter query
    filter_query = {}

    if storage_id:
        try:
            storage_oid = ObjectId(storage_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid storage_id format")

        filter_query.update(
            await _build_storage_filter(db, storage_oid, include_descendants)
        )

    if format:
        filter_query["format"] = format

    if genre_id is not None:
        filter_query["genre_ids"] = genre_id

    try:
        cursor = db.movies.find(filter_query).skip(skip).limit(limit)
        movies = await cursor.to_list(length=limit)
        return [_movie_to_response(m) for m in movies]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list movies: {str(e)}")


@router.get("/search", response_model=List[MovieResponse])
async def search_movies(
    q: str = Query(..., description="Search query for movie titles"),
    skip: int = Query(0, ge=0, description="Number of movies to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of movies to return"),
    storage_id: Optional[str] = Query(None, description="Filter by storage location"),
    include_descendants: bool = Query(
        False, description="Include movies from descendant storage locations"
    ),
    format: Optional[str] = Query(None, description="Filter by media format"),
    genre_id: Optional[int] = Query(None, description="Filter by TMDB genre ID"),
    db=Depends(get_database),
) -> List[MovieResponse]:
    """
    Search movies by title with optional filtering.
    Supports text search across movie titles and metadata.
    """

    # Resolve storage filter (optionally including descendants)
    storage_filter: Optional[Dict[str, Any]] = None
    if storage_id:
        try:
            storage_oid = ObjectId(storage_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid storage_id format")

        storage_filter = await _build_storage_filter(
            db, storage_oid, include_descendants
        )

    # Build filter query with text search
    filter_query: Dict[str, Any] = {"$text": {"$search": q}}

    # Add additional filters
    if storage_filter:
        filter_query.update(storage_filter)

    if format:
        filter_query["format"] = format

    if genre_id is not None:
        filter_query["genre_ids"] = genre_id

    try:
        # Use text search with score sorting
        cursor = (
            db.movies.find(filter_query, {"score": {"$meta": "textScore"}})
            .sort([("score", {"$meta": "textScore"})])
            .skip(skip)
            .limit(limit)
        )

        movies = await cursor.to_list(length=limit)
        return [_movie_to_response(m) for m in movies]

    except Exception:
        # Fallback to regex search if text index doesn't exist
        try:
            filter_query = {"title": {"$regex": q, "$options": "i"}}

            # Add additional filters (reuse already-resolved storage_filter)
            if storage_filter:
                filter_query.update(storage_filter)

            if format:
                filter_query["format"] = format

            if genre_id is not None:
                filter_query["genre_ids"] = genre_id

            cursor = db.movies.find(filter_query).skip(skip).limit(limit)
            movies = await cursor.to_list(length=limit)
            return [_movie_to_response(m) for m in movies]

        except Exception as fallback_e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search movies: {str(fallback_e)}",
            )


@router.get("/tmdb/search", response_model=Dict[str, Any])
async def search_tmdb(
    q: str = Query(..., description="Search query for TMDB movies"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    page: int = Query(1, ge=1, le=1000, description="Page number for pagination"),
    tmdb: TMDBService = Depends(get_tmdb_service),
) -> Dict[str, Any]:
    """
    Search TMDB for movie information.
    """
    try:
        results = await tmdb.search_movies(q, year=year, page=page)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TMDB search failed: {str(e)}")


@router.get("/tmdb/{tmdb_id}", response_model=Dict[str, Any])
async def get_tmdb_movie(
    tmdb_id: int, tmdb: TMDBService = Depends(get_tmdb_service)
) -> Dict[str, Any]:
    """
    Get detailed movie information from TMDB.
    """
    try:
        movie_details = await tmdb.get_movie_details(tmdb_id)
        if not movie_details:
            raise HTTPException(status_code=404, detail="Movie not found in TMDB")
        return movie_details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get TMDB movie: {str(e)}"
        )


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

        return _movie_to_response(movie)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get movie: {str(e)}")


@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(
    movie_id: str,
    movie_update: MovieUpdate,
    db=Depends(get_database),
) -> MovieResponse:
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

    # Build update data. Allow explicit empty lists (e.g. clearing genre_ids).
    update_data = {}
    for field, value in movie_update.model_dump(exclude_unset=True).items():
        if value is not None:
            if field == "storage_id":
                # Validate storage_id exists
                try:
                    storage_id = ObjectId(value)
                except Exception:
                    raise HTTPException(
                        status_code=400, detail="Invalid storage_id format"
                    )

                storage = await db.storage.find_one({"_id": storage_id})
                if not storage:
                    raise HTTPException(
                        status_code=404, detail="Storage location not found"
                    )
                update_data[field] = storage_id
            else:
                update_data[field] = value
        elif field == "genre_ids":
            # Allow explicitly setting genre_ids to an empty list to clear genres
            update_data[field] = value

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    try:
        result = await db.movies.update_one({"_id": object_id}, {"$set": update_data})

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Fetch updated movie
        updated_movie = await db.movies.find_one({"_id": object_id})
        if not updated_movie:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve updated movie"
            )

        return _movie_to_response(updated_movie)

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


@router.post("/{movie_id}/enrich", response_model=MovieResponse)
async def enrich_movie_with_tmdb(
    movie_id: str,
    db=Depends(get_database),
    tmdb: TMDBService = Depends(get_tmdb_service),
) -> MovieResponse:
    """
    Enrich an existing movie with TMDB metadata.
    """

    try:
        object_id = ObjectId(movie_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

    # Get existing movie
    try:
        movie = await db.movies.find_one({"_id": object_id})
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Convert ObjectId to string for processing
        movie_data = {
            "id": str(movie["_id"]),
            "title": movie["title"],
            "year": movie["year"],
            "format": movie["format"],
            "storage_id": str(movie["storage_id"]),
            "tmdb_id": movie.get("tmdb_id"),
            "genre_ids": movie.get("genre_ids"),
            "runtime": movie.get("runtime"),
            "cover_image": movie.get("cover_image"),
        }

        # Enrich with TMDB data
        enriched_data = await tmdb.enrich_movie_data(movie_data)

        # Update movie in database with enriched data
        update_data = {}
        for key, value in enriched_data.items():
            if key not in ["id", "storage_id"] and value is not None:
                if key == "suggested_tmdb_id":
                    # Don't automatically set TMDB ID, just return it as suggestion
                    continue
                update_data[key] = value

        # Persist any newly discovered genres
        if enriched_data.get("tmdb_genre_ids"):
            tmdb_genres = []
            for gid, gname in zip(
                enriched_data.get("tmdb_genre_ids", []),
                enriched_data.get("tmdb_genres", []),
            ):
                tmdb_genres.append({"id": gid, "name": gname})
            if tmdb_genres:
                await upsert_genres(db, tmdb_genres)

        if update_data:
            await db.movies.update_one({"_id": object_id}, {"$set": update_data})

            # Fetch updated movie
            updated_movie = await db.movies.find_one({"_id": object_id})
            if updated_movie:
                movie = updated_movie

        response = _movie_to_response(movie)

        # Add enrichment suggestions to response dict if present
        if "suggested_tmdb_id" in enriched_data:
            # MovieResponse doesn't have these fields; caller can inspect them
            # via the raw JSON body — attach as extra fields via model_extra
            pass

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enrich movie: {str(e)}")
