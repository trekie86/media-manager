"""
Global pytest fixtures and test utilities.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.db.connection import get_database

# Settings fixture
@pytest.fixture
def settings():
    """Get application settings configured for testing."""
    return get_settings()

# Database fixtures
@pytest.fixture
async def db_client(settings) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a test database client."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    try:
        yield client
    finally:
        client.close()

@pytest.fixture
async def test_db(db_client, settings) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Create a test database that's deleted after each test."""
    db = db_client[settings.MONGODB_DB_NAME]
    try:
        yield db
    finally:
        await db_client.drop_database(settings.MONGODB_DB_NAME)

# FastAPI test client fixtures
@pytest.fixture
def app(test_db) -> FastAPI:
    """Create a test FastAPI application."""
    from app.main import app
    
    async def override_get_database():
        yield test_db
    
    app.dependency_overrides[get_database] = override_get_database
    return app

@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

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
        "password": "securepassword123"
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
