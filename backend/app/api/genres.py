"""Genre API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..core.deps import require_approved
from ..db.connection import get_database
from ..models.genre import Genre
from ..models.user import UserInDB

router = APIRouter()


@router.get("/", response_model=List[Genre])
async def list_genres(
    db=Depends(get_database),
    _: UserInDB = Depends(require_approved),
) -> List[Genre]:
    """
    Return all known genres, sorted alphabetically by name.

    The list is pre-seeded from TMDB's canonical genre list on startup and
    grows automatically as new genre IDs are discovered during movie enrichment.
    """
    try:
        cursor = db.genres.find({}, {"_id": 0}).sort("name", 1)
        genres = await cursor.to_list(length=None)
        return [Genre(**g) for g in genres]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list genres: {str(e)}")
