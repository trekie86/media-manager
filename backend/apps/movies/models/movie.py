import uuid
from datetime import date
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class Rating(Enum):
    """The movie rating class that contains an enumeration of values."""

    G = "G"
    PG = "PG"
    PG13 = "PG-13"
    R = "R"
    NC17 = "NC-17"
    NR = "NR"


class Genre(Enum):
    """The movie genre class that contains an enumeration of values."""

    COMEDY = "Comedy"
    DRAMA = "Drama"
    ACTION = "Action"
    ADVENTURE = "Adventure"
    SCIFI = "Sci-Fi"
    HORROR = "Horror"
    SUSPENSE = "Suspense"
    ANIMATED = "Animated"
    CHILDREN = "Children"
    ROMANCE = "Romance"
    FOREIGN = "Foreign"


class Format(Enum):
    """The movie format class that contains an enumeration of values."""

    BLURAY = "Blu-Ray"
    UHDBLURAY = "Ultra HD Blue-Ray"
    DVD = "DVD"
    VHS = "VHS"
    LASERDISC = "Laserdisc"


class UpdateMovie(BaseModel):
    """The update movie model that contains all fields except the id."""

    title: str
    release_date: date
    genre: List[Genre]
    movie_db_id: Optional[int]
    movie_poster_id: Optional[str]
    rating: Rating
    director: Optional[List[str]]
    stars: Optional[List[str]]
    storage_id: Optional[str]
    format: Format

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "title": "Fight Club",
                "genre": ["Drama"],
                "release_date": "1999-10-15",
                "movie_db_id": 550,
                "movie_poster_id": "/a26cQPRhJPX6GbWfQbvZdrrp9j9.jpg",
                "rating": "R",
                "format": "Blu-Ray",
                "stars": ["Brad Pitt", "Edward Norton"],
            }
        }


class Movie(UpdateMovie):
    """The complete movie model that includes the id field."""

    id: str = Field(default_factory=uuid.uuid4, alias="_id")

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "87f0358d-00b1-499f-b8ee-19009eaa0241",
                "title": "Fight Club",
                "genre": ["Drama"],
                "release_date": "1999-10-15",
                "movie_db_id": 550,
                "movie_poster_id": "/a26cQPRhJPX6GbWfQbvZdrrp9j9.jpg",
                "rating": "R",
                "format": "Blu-Ray",
                "stars": ["Brad Pitt", "Edward Norton"],
            }
        }
