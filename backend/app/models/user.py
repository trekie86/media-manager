"""
User models for request/response handling.
"""
from typing import Optional

from pydantic import Field, EmailStr

from .base import MongoModel


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
    password: str = Field(..., description="User password (will be hashed)")


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
