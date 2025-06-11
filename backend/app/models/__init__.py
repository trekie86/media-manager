"""
Models package initialization.
"""
from .base import MongoModel
from .movie import (
    MediaFormat,
    MovieBase,
    MovieCreate,
    MovieUpdate,
    MovieInDB,
    MovieResponse
)
from .bin import (
    BinBase,
    BinCreate,
    BinUpdate,
    BinInDB,
    BinResponse
)
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse
)

__all__ = [
    # Base
    "MongoModel",
    # Movies
    "MediaFormat",
    "MovieBase",
    "MovieCreate",
    "MovieUpdate",
    "MovieInDB",
    "MovieResponse",
    # Bins
    "BinBase",
    "BinCreate",
    "BinUpdate",
    "BinInDB",
    "BinResponse",
    # Users
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
]
