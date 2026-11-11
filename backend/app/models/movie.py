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
    year: int = Field(..., description="Release year", ge=1900, le=2100)
    format: MediaFormat = Field(..., description="Physical media format")
    tmdb_id: Optional[int] = Field(None, description="TMDB movie ID")
    genre_ids: Optional[List[int]] = Field(
        default=None, description="List of TMDB genre IDs"
    )
    runtime: Optional[int] = Field(None, description="Movie runtime in minutes", ge=0)
    cover_image: Optional[str] = Field(None, description="URL to cover image")


class MovieCreate(MovieBase):
    """
    Model for creating a new movie.
    """

    storage_id: str = Field(
        ..., description="ID of the storage location (cabinet, shelf, bin, etc.)"
    )


class MovieUpdate(MongoModel):
    """
    Model for updating an existing movie.
    """

    title: Optional[str] = None
    year: Optional[int] = Field(None, description="Release year", ge=1900, le=2100)
    format: Optional[MediaFormat] = None
    storage_id: Optional[str] = Field(
        None, description="ID of the storage location (cabinet, shelf, bin, etc.)"
    )
    tmdb_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    runtime: Optional[int] = Field(None, description="Movie runtime in minutes", ge=0)
    cover_image: Optional[str] = None


class MovieInDB(MovieBase):
    """
    Model for movie as stored in database.
    """

    storage_id: str = Field(
        ..., description="ID of the storage location (cabinet, shelf, bin, etc.)"
    )


class MovieResponse(MovieInDB):
    """
    Model for movie responses.
    Inherits all fields and adds any API-specific fields.
    """

    pass
