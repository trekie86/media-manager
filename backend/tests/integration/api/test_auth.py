"""Integration tests for authentication routes."""
import pytest
from fastapi import status

from tests.helpers import assert_response, assert_error_response

pytestmark = pytest.mark.asyncio

async def test_register_user_success(client):
    """Test successful user registration."""
    # Test data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123"
    }
    
    # Make request
    response = await client.post("/api/auth/register", json=user_data)
    
    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_201_CREATED,
        expected_content={
            "id": None,  # MongoModel includes id field
            "username": user_data["username"],
            "email": user_data["email"]
        }
    )

async def test_register_user_duplicate_username(client):
    """Test registration with duplicate username fails."""
    # Test data
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "securepass123"
    }
    
    # Create first user
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Try to create duplicate user
    response = await client.post("/api/auth/register", json=user_data)
    
    # Assert error response
    assert_error_response(
        response,
        expected_status_code=status.HTTP_400_BAD_REQUEST,
        expected_detail="Username already registered"
    )

async def test_register_user_invalid_data(client):
    """Test registration with invalid data fails."""
    # Test cases with invalid data
    test_cases = [
        (
            {"username": "t", "email": "test@example.com", "password": "pass123"},
            "Value error, Username must be at least 3 characters long"
        ),
        (
            {"username": "test", "email": "invalid-email", "password": "pass123"},
            "value is not a valid email address: An email address must have an @-sign."
        ),
        (
            {"username": "test", "email": "test@example.com", "password": "short"},
            "String should have at least 8 characters"
        )
    ]
    
    for data, expected_detail in test_cases:
        response = await client.post("/api/auth/register", json=data)
        print(f"Response for {data}: {response.json()}")  # Debug print
        assert_error_response(
            response,
            expected_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            expected_detail=expected_detail
        )

async def test_login_success(client):
    """Test successful user login."""
    # Create test user
    user_data = {
        "username": "logintest",
        "email": "login@example.com",
        "password": "securepass123"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Test login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = await client.post("/api/auth/login", json=login_data)
    
    # Assert response
    assert_response(
        response,
        expected_status_code=status.HTTP_200_OK
    )
    
    # Verify response contains access token
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

async def test_login_invalid_credentials(client):
    """Test login with invalid credentials fails."""
    # Test cases with invalid credentials
    test_cases = [
        {
            "username": "nonexistent",
            "password": "wrongpass123"
        },
        {
            "username": "testuser",  # Assuming this user exists from previous test
            "password": "wrongpassword"
        }
    ]
    
    for data in test_cases:
        response = await client.post("/api/auth/login", json=data)
        assert_error_response(
            response,
            expected_status_code=status.HTTP_401_UNAUTHORIZED,
            expected_detail="Invalid username or password"
        )
