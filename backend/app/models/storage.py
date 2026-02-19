"""
Storage models for request/response handling.
"""

from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import Field, BaseModel, model_validator

from .base import MongoModel
from .movie import MovieResponse


class StorageType(str, Enum):
    """
    Enumeration of storage types.
    """

    CABINET = "cabinet"
    SHELF = "shelf"
    BIN = "bin"
    DRAWER = "drawer"


class StorageMetadata(BaseModel):
    """
    Optional metadata for storage locations.
    """

    capacity: Optional[int] = Field(
        None,
        description="Storage capacity (if applicable)",
        ge=0,  # Must be greater than or equal to 0
    )
    dimensions: Optional[str] = Field(None, description="Physical dimensions")
    location: Optional[str] = Field(
        None, description="Physical location or coordinates"
    )
    custom: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata fields specific to storage type",
    )


class StorageBase(MongoModel):
    """
    Base storage model with shared attributes.
    """

    name: str = Field(..., description="Storage location name")
    description: Optional[str] = Field(None, description="Storage description")
    type: StorageType = Field(..., description="Type of storage location")
    parent_id: Optional[str] = Field(None, description="ID of parent storage location")
    path: List[str] = Field(
        default_factory=list,
        description="Materialized path of ancestor IDs for efficient tree operations",
    )
    metadata: StorageMetadata = Field(
        default_factory=StorageMetadata,
        description="Optional metadata specific to the storage type",
    )

    @model_validator(mode="after")
    def validate_path_with_parent(self) -> "StorageBase":
        """Ensure path is valid when parent_id is present."""
        if self.parent_id and not self.path:
            raise ValueError("Path cannot be empty when parent_id is set")
        if self.parent_id and self.parent_id not in self.path:
            raise ValueError("Path must contain parent_id")
        return self


class StorageCreate(StorageBase):
    """
    Model for creating a new storage location.
    """

    pass


class StorageUpdate(MongoModel):
    """
    Model for updating an existing storage location.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[StorageType] = None
    parent_id: Optional[str] = None
    metadata: Optional[StorageMetadata] = None

    @model_validator(mode="after")
    def validate_parent_id(self) -> "StorageUpdate":
        """Ensure parent_id is not set to create a cycle."""
        # Note: Full cycle detection will be handled in the service layer
        if self.parent_id and self.parent_id == str(self.id):
            raise ValueError("Storage location cannot be its own parent")
        return self


class StorageInDB(StorageBase):
    """
    Model for storage as stored in database.
    """

    pass


class StorageResponse(StorageInDB):
    """
    Model for storage responses.
    Can optionally include the movies stored in this location
    and immediate children storage locations.
    """

    movies: Optional[List[MovieResponse]] = Field(
        default_factory=list, description="List of movies stored in this location"
    )
    children: List["StorageResponse"] = Field(
        default_factory=list, description="List of immediate child storage locations"
    )


class StorageTreeResponse(StorageResponse):
    """
    Model for full tree responses.
    Includes complete subtree of storage locations.
    """

    descendants: List[StorageResponse] = Field(
        default_factory=list, description="List of all descendant storage locations"
    )
    ancestors: List[StorageResponse] = Field(
        default_factory=list, description="List of all ancestor storage locations"
    )


# No need for update_forward_refs() in Pydantic v2
# Forward references are handled automatically
