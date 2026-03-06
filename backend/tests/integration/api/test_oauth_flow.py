"""Integration tests for OAuth auth flow and RBAC enforcement."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_get_me_authenticated(auth_client):
    """GET /api/auth/me returns user info for an authenticated user."""
    response = await auth_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert data["role"] == "read_only"
    assert data["status"] == "approved"


async def test_get_me_admin(admin_client):
    """GET /api/auth/me returns admin info for an admin user."""
    response = await admin_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"
    assert data["status"] == "approved"


async def test_get_me_unauthenticated(client):
    """GET /api/auth/me returns 401 when no token is provided."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_get_me_invalid_token(client):
    """GET /api/auth/me returns 401 for an invalid token."""
    client.headers["Authorization"] = "Bearer invalid.token.here"
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_logout(auth_client):
    """POST /api/auth/logout returns success for authenticated user."""
    response = await auth_client.post("/api/auth/logout")
    assert response.status_code == 200


async def test_read_only_user_can_read_movies(auth_client, test_db):
    """Approved read-only user can access GET /api/movies/."""
    response = await auth_client.get("/api/movies/")
    assert response.status_code == 200


async def test_read_only_user_cannot_create_movie(auth_client, test_db, sample_storage_data):
    """Read-only user gets 403 when trying to POST /api/movies/."""
    # Insert a storage so we have a valid ID
    from bson import ObjectId
    storage_result = await test_db.storage.insert_one({
        "name": "Storage for test", "type": "cabinet", "path": []
    })
    movie_data = {
        "title": "Test Movie",
        "year": 2020,
        "format": "DVD",
        "storage_id": str(storage_result.inserted_id),
    }
    response = await auth_client.post("/api/movies/", json=movie_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


async def test_unauthenticated_user_cannot_read_movies(client):
    """Unauthenticated request to GET /api/movies/ returns 401."""
    response = await client.get("/api/movies/")
    assert response.status_code == 401


async def test_admin_can_list_pending_users(admin_client, test_db):
    """Admin can list pending users."""
    # Insert a pending user
    from datetime import datetime, timezone
    await test_db.users.insert_one({
        "email": "pending@example.com",
        "display_name": "Pending User",
        "provider": "google",
        "provider_id": "google_pending_001",
        "role": "read_only",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    })

    response = await admin_client.get("/api/auth/users/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "pending@example.com"
    assert data[0]["status"] == "pending"


async def test_read_only_cannot_list_pending_users(auth_client):
    """Read-only user cannot access pending users list."""
    response = await auth_client.get("/api/auth/users/pending")
    assert response.status_code == 403


async def test_admin_can_approve_user(admin_client, test_db):
    """Admin can approve a pending user."""
    from datetime import datetime, timezone
    from bson import ObjectId
    result = await test_db.users.insert_one({
        "email": "pending2@example.com",
        "display_name": "Pending 2",
        "provider": "github",
        "provider_id": "github_pending_002",
        "role": "read_only",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    })
    user_id = str(result.inserted_id)

    response = await admin_client.post(f"/api/auth/users/{user_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_admin_can_reject_user(admin_client, test_db):
    """Admin can reject (delete) a pending user."""
    from datetime import datetime, timezone
    result = await test_db.users.insert_one({
        "email": "reject@example.com",
        "display_name": "To Reject",
        "provider": "google",
        "provider_id": "google_reject_003",
        "role": "read_only",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    })
    user_id = str(result.inserted_id)

    response = await admin_client.post(f"/api/auth/users/{user_id}/reject")
    assert response.status_code == 204

    # Verify deleted
    doc = await test_db.users.find_one({"_id": result.inserted_id})
    assert doc is None
