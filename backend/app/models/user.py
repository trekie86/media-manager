"""
User models for OAuth authentication and role-based access control.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field, EmailStr

from .base import MongoModel


class OAuthProvider(str, Enum):
    google = "google"
    github = "github"


class UserRole(str, Enum):
    admin = "admin"
    read_only = "read_only"


class UserStatus(str, Enum):
    pending = "pending"
    approved = "approved"


# Auth specific models
class TokenResponse(MongoModel):
    """Authentication token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class UserInDB(MongoModel):
    """Model for user as stored in database."""

    email: EmailStr = Field(..., description="User email address from OAuth provider")
    display_name: str = Field(..., description="Display name from OAuth provider")
    avatar_url: Optional[str] = Field(None, description="Avatar URL from OAuth provider")
    provider: OAuthProvider = Field(..., description="OAuth provider used to authenticate")
    provider_id: str = Field(..., description="Stable user ID from the OAuth provider")
    role: UserRole = Field(UserRole.read_only, description="User role")
    status: UserStatus = Field(UserStatus.pending, description="Account approval status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: datetime = Field(..., description="Last login timestamp")


class UserResponse(MongoModel):
    """Model for user responses (excludes sensitive internal fields)."""

    email: EmailStr = Field(..., description="User email address")
    display_name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="Account approval status")
