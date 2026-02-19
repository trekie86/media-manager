"""
Global pytest fixtures and test utilities.
"""
import asyncio
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
    # Use the test database
    db = db_client[settings.MONGO_DB]
    
    try:
        # Clear collections instead of dropping the database
        collections = await db.list_collection_names()
        for collection in collections:
            if collection != "system.users":  # Skip system collections
                await db[collection].delete_many({})
        
        # Initialize indexes with correct options
        await db.users.create_index("username", unique=True)
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

# Auth fixtures
@pytest.fixture
async def test_user(client, sample_user_data) -> dict:
    """Create a test user and return their data."""
    response = await client.post("/api/auth/register", json=sample_user_data)
    assert response.status_code == 201
    return sample_user_data

@pytest.fixture
async def auth_token(client, test_user) -> str:
    """Get an authentication token for the test user."""
    response = await client.post("/api/auth/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
async def auth_client(client, auth_token) -> AsyncClient:
    """Get an authenticated client for testing protected endpoints."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
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
        "genre": ["Action", "Sci-Fi"],
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

@pytest.fixture
async def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123"
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
