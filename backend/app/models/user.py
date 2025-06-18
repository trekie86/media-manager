"""
User models for request/response handling and authentication.
"""
import re
from typing import Optional

from pydantic import Field, EmailStr, field_validator

from .base import MongoModel

# Auth specific models
class TokenResponse(MongoModel):
    """Authentication token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")

class UserLogin(MongoModel):
    """User login request model."""
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="Password")


class UserBase(MongoModel):
    """
    Base user model with shared attributes.
    """
    username: str = Field(..., description="Username for login")
    email: Optional[EmailStr] = Field(None, description="User email address")


class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=8, description="User password (will be hashed)")

    @field_validator("username")
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(MongoModel):
    """
    Model for updating an existing user.
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """
    Model for user as stored in database.
    """
    password_hash: str = Field(..., description="Hashed password")


class UserResponse(UserBase):
    """
    Model for user responses.
    Excludes sensitive information like password hash.
    """
    pass
