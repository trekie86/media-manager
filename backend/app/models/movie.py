"""
Movie models for request/response handling.
"""
from enum import Enum
from typing import List, Optional

from pydantic import Field

from .base import MongoModel


class MediaFormat(str, Enum):
    """
    Supported physical media formats.
    """
    DVD = "DVD"
    BLURAY = "Blu-ray"
    DIGITAL = "Digital"


class MovieBase(MongoModel):
    """
    Base movie model with shared attributes.
    """
    title: str = Field(..., description="Movie title")
    year: int = Field(..., description="Release year")
    format: MediaFormat = Field(..., description="Physical media format")
    tmdb_id: Optional[int] = Field(None, description="TMDB movie ID")
    genre: Optional[List[str]] = Field(default=None, description="List of genres")
    runtime: Optional[int] = Field(None, description="Movie runtime in minutes")
    cover_image: Optional[str] = Field(None, description="URL to cover image")


class MovieCreate(MovieBase):
    """
    Model for creating a new movie.
    """
    storage_id: str = Field(
        ...,
        description="ID of the storage location (cabinet, shelf, bin, etc.)"
    )


class MovieUpdate(MongoModel):
    """
    Model for updating an existing movie.
    """
    title: Optional[str] = None
    year: Optional[int] = None
    format: Optional[MediaFormat] = None
    storage_id: Optional[str] = Field(
        None,
        description="ID of the storage location (cabinet, shelf, bin, etc.)"
    )
    tmdb_id: Optional[int] = None
    genre: Optional[List[str]] = None
    runtime: Optional[int] = None
    cover_image: Optional[str] = None


class MovieInDB(MovieBase):
    """
    Model for movie as stored in database.
    """
    storage_id: str = Field(
        ...,
        description="ID of the storage location (cabinet, shelf, bin, etc.)"
    )


class MovieResponse(MovieInDB):
    """
    Model for movie responses.
    Inherits all fields and adds any API-specific fields.
    """
    pass
