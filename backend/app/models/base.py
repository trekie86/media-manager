"""
Base models and shared utilities.
"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MongoModel(BaseModel):
    """
    Base model with MongoDB configuration.
    Handles ObjectId conversion and provides common fields.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        },
        populate_by_name=True
    )
    
    id: Optional[str] = None

    def dict(self, *args, **kwargs):
        """Convert model to dict, transforming 'id' to '_id' for MongoDB."""
        data = super().dict(*args, **kwargs)
        # Only include id/_id if it's set
        if self.id:
            data["_id"] = self.id
        if "_id" in data and not data["_id"]:
            del data["_id"]
        if "id" in data:
            del data["id"]
        return data
