"""Unit tests for OAuth-based user models."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.models.user import (
    UserInDB,
    UserResponse,
    OAuthProvider,
    UserRole,
    UserStatus,
)

pytestmark = pytest.mark.unit


def _make_user(**kwargs) -> dict:
    defaults = {
        "email": "user@example.com",
        "display_name": "Test User",
        "avatar_url": None,
        "provider": OAuthProvider.google,
        "provider_id": "google_123",
        "role": UserRole.read_only,
        "status": UserStatus.approved,
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return defaults


def test_user_in_db_valid():
    """UserInDB accepts valid OAuth user data."""
    user = UserInDB(**_make_user())
    assert user.email == "user@example.com"
    assert user.provider == OAuthProvider.google
    assert user.role == UserRole.read_only
    assert user.status == UserStatus.approved


def test_user_in_db_github_provider():
    """UserInDB accepts GitHub as provider."""
    user = UserInDB(**_make_user(provider=OAuthProvider.github, provider_id="gh_456"))
    assert user.provider == OAuthProvider.github


def test_user_in_db_admin_role():
    """UserInDB accepts admin role."""
    user = UserInDB(**_make_user(role=UserRole.admin))
    assert user.role == UserRole.admin


def test_user_in_db_pending_status():
    """UserInDB accepts pending status."""
    user = UserInDB(**_make_user(status=UserStatus.pending))
    assert user.status == UserStatus.pending


def test_user_in_db_invalid_email():
    """UserInDB rejects invalid email."""
    with pytest.raises(ValidationError):
        UserInDB(**_make_user(email="not-an-email"))


def test_user_in_db_invalid_provider():
    """UserInDB rejects unknown provider."""
    with pytest.raises(ValidationError):
        UserInDB(**_make_user(provider="twitter"))


def test_user_in_db_invalid_role():
    """UserInDB rejects unknown role."""
    with pytest.raises(ValidationError):
        UserInDB(**_make_user(role="superuser"))


def test_user_response_excludes_internal_fields():
    """UserResponse does not expose provider_id, created_at, last_login."""
    resp = UserResponse(
        email="user@example.com",
        display_name="Test User",
        role=UserRole.read_only,
        status=UserStatus.approved,
    )
    fields = set(resp.model_fields.keys())
    assert "provider_id" not in fields
    assert "created_at" not in fields
    assert "last_login" not in fields


def test_user_response_optional_avatar():
    """UserResponse allows optional avatar_url."""
    resp = UserResponse(
        email="user@example.com",
        display_name="Test User",
        role=UserRole.admin,
        status=UserStatus.approved,
        avatar_url="https://example.com/avatar.png",
    )
    assert resp.avatar_url == "https://example.com/avatar.png"

    resp_no_avatar = UserResponse(
        email="user@example.com",
        display_name="Test User",
        role=UserRole.admin,
        status=UserStatus.approved,
    )
    assert resp_no_avatar.avatar_url is None
