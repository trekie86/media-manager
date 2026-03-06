"""
Global pytest fixtures and test utilities.
"""
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.db.connection import get_database
from app.services.tmdb import get_tmdb_service

# Settings fixture
@pytest.fixture
def settings():
    """Get application settings configured for testing."""
    return get_settings()

# Database fixtures
@pytest.fixture
async def db_client(settings) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a test database client."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    try:
        yield client
    finally:
        client.close()

# Import these at the top level
from app.db.connection import connect_to_mongo, close_mongo_connection

@pytest.fixture
async def test_db(db_client, settings) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Create a test database that's deleted after each test."""
    db = db_client[settings.MONGO_DB]

    try:
        # Clear collections before each test
        collections = await db.list_collection_names()
        for collection in collections:
            if collection != "system.users":
                await db[collection].delete_many({})

        # Initialize indexes with new OAuth-based schema
        await db.users.create_index([("provider", 1), ("provider_id", 1)], unique=True)
        await db.users.create_index("email", unique=True, sparse=True)

        # Initialize the database connection
        await connect_to_mongo()

        yield db
    finally:
        await close_mongo_connection()

@pytest.fixture
def mock_tmdb_service():
    """Mock TMDB service that makes no live API calls."""
    service = MagicMock()
    service.get_movie_details = AsyncMock(return_value=None)
    service.search_movies = AsyncMock(return_value={"results": [], "total_results": 0, "total_pages": 0})
    service.enrich_movie_data = AsyncMock(side_effect=lambda d: d)
    return service


# FastAPI test client fixtures
@pytest.fixture
def app(test_db, mock_tmdb_service) -> FastAPI:
    """Create a test FastAPI application."""
    from app.main import app

    async def override_get_database():
        yield test_db

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_tmdb_service] = lambda: mock_tmdb_service
    return app

@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        yield client

# Auth fixtures — bypass OAuth by inserting users directly and creating JWTs
@pytest.fixture
async def sample_user_data() -> dict:
    """Sample approved read-only user data for testing."""
    return {
        "email": "test@example.com",
        "display_name": "Test User",
        "provider": "google",
        "provider_id": "google_123456",
        "role": "read_only",
        "status": "approved",
    }

@pytest.fixture
async def sample_admin_data() -> dict:
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "display_name": "Admin User",
        "provider": "google",
        "provider_id": "google_admin_789",
        "role": "admin",
        "status": "approved",
    }

@pytest.fixture
async def test_user(test_db, sample_user_data) -> dict:
    """Insert a read-only approved user directly into the DB, bypassing OAuth."""
    doc = {
        **sample_user_data,
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    }
    await test_db.users.insert_one(doc)
    return sample_user_data

@pytest.fixture
async def test_admin(test_db, sample_admin_data) -> dict:
    """Insert an admin user directly into the DB, bypassing OAuth."""
    doc = {
        **sample_admin_data,
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    }
    await test_db.users.insert_one(doc)
    return sample_admin_data

@pytest.fixture
def auth_token(test_user) -> str:
    """Create a JWT directly for the read-only test user, bypassing OAuth."""
    from app.api.auth import create_access_token
    return create_access_token({
        "sub": test_user["email"],
        "role": test_user["role"],
        "status": test_user["status"],
    })

@pytest.fixture
def admin_token(test_admin) -> str:
    """Create a JWT directly for the admin test user, bypassing OAuth."""
    from app.api.auth import create_access_token
    return create_access_token({
        "sub": test_admin["email"],
        "role": test_admin["role"],
        "status": test_admin["status"],
    })

@pytest.fixture
async def auth_client(client, auth_token) -> AsyncClient:
    """Get an authenticated client (read-only user) for testing protected endpoints."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client

@pytest.fixture
async def admin_client(client, admin_token) -> AsyncClient:
    """Get an authenticated client (admin user) for testing write endpoints."""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client

# Test data fixtures
@pytest.fixture
async def sample_movie_data() -> dict:
    """Sample movie data for testing."""
    from app.models.movie import MediaFormat
    return {
        "title": "Test Movie",
        "year": 2025,
        "format": MediaFormat.DVD.value,
        "tmdb_id": 12345,
        "genre_ids": [28, 878],
        "runtime": 120,
        "cover_image": "http://example.com/poster.jpg"
    }

@pytest.fixture
async def sample_storage_data() -> dict:
    """Sample storage data for testing."""
    return {
        "name": "Test Cabinet",
        "description": "A test storage cabinet",
        "type": "cabinet",
        "metadata": {
            "capacity": 100,
            "dimensions": "100x50x200cm",
            "location": "Living Room"
        }
    }

# Utility functions
def pytest_configure(config):
    """Add custom markers."""
    markers = [
        "unit",
        "integration",
        "functional",
        "performance",
        "slow",
        "db",
        "tmdb",
        "auth",
    ]
    for marker in markers:
        config.addinivalue_line("markers", f"{marker}: mark test as {marker} type")

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
