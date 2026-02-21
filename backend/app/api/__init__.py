"""API route handlers for the Media Manager application."""

from fastapi import APIRouter

from .auth import router as auth_router
from .genres import router as genres_router
from .movies import router as movies_router
from .storage import router as storage_router

# Create the main API router
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(genres_router, prefix="/genres", tags=["genres"])
api_router.include_router(movies_router, prefix="/movies", tags=["movies"])
api_router.include_router(storage_router, prefix="/storage", tags=["storage"])
