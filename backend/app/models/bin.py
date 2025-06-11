"""
Storage bin models for request/response handling.
"""
from typing import Optional, List

from pydantic import Field

from .base import MongoModel
from .movie import MovieResponse


class BinBase(MongoModel):
    """
    Base bin model with shared attributes.
    """
    name: str = Field(..., description="Bin name")
    description: Optional[str] = Field(None, description="Bin description")


class BinCreate(BinBase):
    """
    Model for creating a new storage bin.
    """
    pass


class BinUpdate(MongoModel):
    """
    Model for updating an existing storage bin.
    """
    name: Optional[str] = None
    description: Optional[str] = None


class BinInDB(BinBase):
    """
    Model for bin as stored in database.
    """
    pass


class BinResponse(BinInDB):
    """
    Model for bin responses.
    Can optionally include the movies stored in the bin.
    """
    movies: Optional[List[MovieResponse]] = Field(
        default=None,
        description="List of movies stored in this bin"
    )
